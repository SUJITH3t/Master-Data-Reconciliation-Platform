"""
Unit and Integration Tests for Real-Time Streaming Ingestion and Debezium CDC Processing.
"""

import time
import pytest
from services.streaming_ingestion import DebeziumCDCParser, StreamingIngestionEngine, streaming_engine


def test_debezium_cdc_parser_product_insert():
    """Verify Debezium CDC JSON parsing for a create operation."""
    payload = {
        "payload": {
            "op": "c",
            "source": {
                "connector": "postgresql-debezium",
                "db": "retail_pos",
                "table": "store_inventory",
                "ts_ms": int((time.time() - 0.25) * 1000)
            },
            "after": {
                "sku": "SKU-TEST-100",
                "name": "Wireless Noise Cancelling Headphones",
                "price": 199.99
            }
        }
    }
    parsed = DebeziumCDCParser.parse_event(payload)
    assert parsed["op"] == "c"
    assert parsed["record_type"] == "Product"
    assert parsed["business_identifier"] == "SKU-TEST-100"
    assert parsed["source_system"] == "Store Inventory POS"
    assert parsed["lag_ms"] >= 0.0


def test_debezium_cdc_parser_customer_update():
    """Verify Debezium CDC parsing for customer update event from ERP."""
    payload = {
        "payload": {
            "op": "u",
            "source": {
                "connector": "oracle-erp-cdc",
                "db": "erp_prod",
                "table": "customers",
                "ts_ms": int((time.time() - 0.1) * 1000)
            },
            "after": {
                "customer_id": "CUST-STREAM-01",
                "name": "Elena Rostova",
                "email": "elena.r@enterprise.com",
                "phone": "555-987-6543"
            }
        }
    }
    parsed = DebeziumCDCParser.parse_event(payload)
    assert parsed["op"] == "u"
    assert parsed["record_type"] == "Customer"
    assert parsed["business_identifier"] == "CUST-STREAM-01"
    assert parsed["source_system"] == "ERP"


def test_streaming_engine_enqueue_and_metrics():
    """Verify asynchronous enqueueing and telemetry reporting."""
    payload = {
        "payload": {
            "op": "u",
            "source": {
                "connector": "mysql-shopify",
                "table": "ecommerce_orders",
                "ts_ms": int((time.time() - 0.05) * 1000)
            },
            "after": {
                "customer_id": "CUST-STREAM-02",
                "name": "Marcus Vance",
                "email": "marcus.v@demo.com"
            }
        }
    }
    res = streaming_engine.enqueue_cdc_event(payload)
    assert res["status"] == "QUEUED"
    assert "event_id" in res

    time.sleep(0.5)  # Allow background worker to process
    metrics = streaming_engine.get_stream_metrics()
    assert metrics["total_ingested"] >= 1
    assert metrics["worker_status"] == "ACTIVE_RUNNING"
    assert metrics["dead_letter_queue_count"] == 0
