"""
W3C PROV-O Compliant Data Lineage & Provenance Tracking Service.
Tracks the end-to-end data lifecycle from raw source feeds (ERP, POS, Shopify, Logistics)
through normalization, probabilistic linkage, survivorship resolution, governance approval,
and final publication into the Golden Master Record.
"""

from typing import Any, Dict, List, Optional
from database.database import execute_query


class ProvenanceNodeType:
    SOURCE_FEED = "SOURCE_FEED"
    INGESTED_RECORD = "INGESTED_RECORD"
    NORMALIZED_ENTITY = "NORMALIZED_ENTITY"
    RECONCILIATION_CASE = "RECONCILIATION_CASE"
    APPROVAL_DECISION = "APPROVAL_DECISION"
    GOLDEN_MASTER = "GOLDEN_MASTER"
    AGENT = "AGENT"


class LineageService:
    """Constructs Directed Acyclic Graph (DAG) provenance chains for master entities."""

    @staticmethod
    def get_entity_provenance(record_type: str, business_id: str) -> Dict[str, Any]:
        """
        Builds a W3C PROV-O compliant provenance tree for a specific master record:
        - Entity: Artifacts generated or consumed
        - Activity: Processing stages (Ingest, Normalization, Survivorship, Approval, Publish)
        - Agent: Systems and Human Stewards responsible
        """
        b_id = business_id.strip()

        # 1. Fetch Golden Master Record
        tbl = "customers" if record_type == "Customer" else ("products" if record_type == "Product" else "suppliers")
        golden_rows = execute_query(f"SELECT * FROM {tbl} WHERE business_id = ?", (b_id,))
        golden_rec = dict(golden_rows[0]) if golden_rows else None

        # 2. Fetch Contributing Source Records
        src_rows = execute_query(
            "SELECT * FROM source_records WHERE business_identifier = ? AND record_type = ? ORDER BY id ASC",
            (b_id, record_type)
        )
        source_records = [dict(r) for r in src_rows]

        # 3. Fetch Reconciliation Cases
        case_rows = execute_query(
            "SELECT * FROM reconciliation_cases WHERE business_id = ? AND record_type = ? ORDER BY id ASC",
            (b_id, record_type)
        )
        cases = [dict(r) for r in case_rows]

        # 4. Fetch Approvals & Audit Trail
        audit_rows = execute_query(
            "SELECT * FROM audit_logs WHERE business_id = ? AND record_type = ? ORDER BY id ASC",
            (b_id, record_type)
        )
        audit_trail = [dict(r) for r in audit_rows]

        # 5. Build W3C PROV-O Graph Elements (Nodes & Edges)
        nodes = []
        edges = []

        # Master Node
        master_node_id = f"golden_{record_type}_{b_id}"
        nodes.append({
            "id": master_node_id,
            "label": f"Golden Master\n{b_id}",
            "type": ProvenanceNodeType.GOLDEN_MASTER,
            "prov_type": "prov:Entity",
            "metadata": golden_rec or {"status": "Unpublished"}
        })

        # Source Systems & Feed Nodes
        for i, src in enumerate(source_records):
            src_node_id = f"src_{src.get('source_system', 'src')}_{src.get('id', i)}"
            nodes.append({
                "id": src_node_id,
                "label": f"{src.get('source_system', 'Source')}\n(Ingested)",
                "type": ProvenanceNodeType.SOURCE_FEED,
                "prov_type": "prov:Entity",
                "metadata": {
                    "source_system": src.get("source_system"),
                    "timestamp": src.get("source_timestamp"),
                    "verification": src.get("verification_status"),
                    "raw_fields": src.get("field_values_json") or src.get("field_values")
                }
            })

            # Activity Node: Ingestion & Normalization
            act_id = f"act_norm_{src.get('id', i)}"
            nodes.append({
                "id": act_id,
                "label": "Normalization\nPipeline",
                "type": ProvenanceNodeType.NORMALIZED_ENTITY,
                "prov_type": "prov:Activity",
                "metadata": {"stage": "Data Cleansing & Type Standardization"}
            })

            edges.append({"source": src_node_id, "target": act_id, "relation": "prov:used"})

            # Link to reconciliation case if available
            matching_case = next((c for c in cases if c.get("recommended_source") == src.get("source_system")), None)
            if matching_case:
                case_node_id = f"case_{matching_case.get('id')}"
                edges.append({"source": act_id, "target": case_node_id, "relation": "prov:wasInformedBy"})

        # Reconciliation Case Nodes
        for case in cases:
            case_node_id = f"case_{case.get('id')}"
            attr = case.get("field_name") or case.get("attribute_name") or "Attribute"
            conf = case.get("confidence_score") or 90.0
            nodes.append({
                "id": case_node_id,
                "label": f"Survivorship: {attr}\nConf: {conf}%",
                "type": ProvenanceNodeType.RECONCILIATION_CASE,
                "prov_type": "prov:Activity",
                "metadata": {
                    "attribute": attr,
                    "winner": case.get("recommended_value"),
                    "winning_source": case.get("recommended_source"),
                    "rationale": case.get("rationale"),
                    "confidence": conf
                }
            })

            # Edge from Case to Master Record
            edges.append({"source": case_node_id, "target": master_node_id, "relation": "prov:wasGeneratedBy"})

        # Human Reviewer & Agent Nodes from Audit Trail
        for audit in audit_trail:
            if audit["action"] in ("APPROVE_RECOMMENDATION", "PUBLISH_RECORD", "REJECT_RECOMMENDATION"):
                agent_id = f"agent_{audit['user_email']}"
                if not any(n["id"] == agent_id for n in nodes):
                    nodes.append({
                        "id": agent_id,
                        "label": f"Reviewer Agent\n{audit['user_email']}",
                        "type": ProvenanceNodeType.AGENT,
                        "prov_type": "prov:Agent",
                        "metadata": {"role": audit["role"], "email": audit["user_email"]}
                    })
                edges.append({"source": agent_id, "target": master_node_id, "relation": "prov:wasAttributedTo"})

        return {
            "business_id": b_id,
            "record_type": record_type,
            "prov_standard": "W3C PROV-O (Provenance Ontology)",
            "total_contributing_sources": len(source_records),
            "reconciliation_cases_count": len(cases),
            "audit_events_count": len(audit_trail),
            "graph": {
                "nodes": nodes,
                "edges": edges
            }
        }
