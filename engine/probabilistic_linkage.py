"""
Probabilistic Record Linkage and Typo-Tolerant Entity Matching Engine.
Implements the Fellegi-Sunter methodology with Jaro-Winkler, Character N-gram Cosine
similarity, Levenshtein distance, and phonetic Soundex blocking.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple


# =====================================================================
# 1. String Distance & Similarity Algorithms
# =====================================================================

def soundex(text: Optional[str]) -> str:
    """Computes the American Soundex phonetic code for string blocking."""
    if not text:
        return "0000"
    s = re.sub(r"[^A-Za-z]", "", str(text)).upper()
    if not s:
        return "0000"

    mapping = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6"
    }

    first = s[0]
    encoded = [first]
    prev_code = mapping.get(first, "0")

    for char in s[1:]:
        code = mapping.get(char, "0")
        if code != "0" and code != prev_code:
            encoded.append(code)
            if len(encoded) == 4:
                break
        prev_code = code

    while len(encoded) < 4:
        encoded.append("0")

    return "".join(encoded)


def levenshtein_distance(s1: Optional[str], s2: Optional[str]) -> int:
    """Calculates Levenshtein edit distance."""
    if not s1:
        return len(s2) if s2 else 0
    if not s2:
        return len(s1)
    
    s1, s2 = s1.lower(), s2.lower()
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Deletion
                dp[i][j - 1] + 1,       # Insertion
                dp[i - 1][j - 1] + cost # Substitution
            )
    return dp[m][n]


def jaro_similarity(s1: Optional[str], s2: Optional[str]) -> float:
    """Computes standard Jaro similarity between two strings."""
    if not s1 or not s2:
        return 0.0
    s1, s2 = s1.lower().strip(), s2.lower().strip()
    if s1 == s2:
        return 1.0

    len1, len2 = len(s1), len(s2)
    max_dist = max(len1, len2) // 2 - 1
    if max_dist < 0:
        max_dist = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0

    for i in range(len1):
        start = max(0, i - max_dist)
        end = min(i + max_dist + 1, len2)
        for j in range(start, end):
            if not s2_matches[j] and s1[i] == s2[j]:
                s1_matches[i] = True
                s2_matches[j] = True
                matches += 1
                break

    if matches == 0:
        return 0.0

    # Count transpositions
    k = 0
    transpositions = 0
    for i in range(len1):
        if s1_matches[i]:
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1

    transpositions //= 2
    return (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3.0


def jaro_winkler_similarity(s1: Optional[str], s2: Optional[str], prefix_weight: float = 0.1) -> float:
    """
    Computes Jaro-Winkler similarity, providing a boost for common prefixes.
    Ideal for person names and typo-tolerant matching.
    """
    jaro = jaro_similarity(s1, s2)
    if not s1 or not s2:
        return jaro

    s1, s2 = s1.lower().strip(), s2.lower().strip()
    # Find prefix length (up to 4 characters)
    prefix_len = 0
    for c1, c2 in zip(s1[:4], s2[:4]):
        if c1 == c2:
            prefix_len += 1
        else:
            break

    return jaro + (prefix_len * prefix_weight * (1.0 - jaro))


def get_character_ngrams(text: str, n: int = 3) -> Dict[str, int]:
    """Generates character n-grams with frequency count."""
    cleaned = f"  {text.lower().strip()}  "
    counts = {}
    for i in range(len(cleaned) - n + 1):
        gram = cleaned[i:i + n]
        counts[gram] = counts.get(gram, 0) + 1
    return counts


def cosine_similarity_ngrams(s1: Optional[str], s2: Optional[str], n: int = 3) -> float:
    """
    Calculates cosine similarity on character n-grams.
    Resilient to token reordering, missing street suffixes, and typos.
    """
    if not s1 or not s2:
        return 0.0
    s1_clean = str(s1).strip().lower()
    s2_clean = str(s2).strip().lower()
    if s1_clean == s2_clean:
        return 1.0

    vec1 = get_character_ngrams(s1_clean, n=n)
    vec2 = get_character_ngrams(s2_clean, n=n)

    all_keys = set(vec1.keys()).union(set(vec2.keys()))
    dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in all_keys)
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)


# =====================================================================
# 2. Fellegi-Sunter Probabilistic Record Linkage Methodology
# =====================================================================

class FellegiSunterModel:
    """
    Implementation of the classic Fellegi-Sunter (1969) record linkage framework.
    Calculates agreement (w+) and disagreement (w-) weights based on m and u probabilities:
      m = P(agree | Match)
      u = P(agree | Non-Match)
      w+ = log2(m / u)
      w- = log2((1 - m) / (1 - u))
    """

    # Field baseline parameters: (m_prob, u_prob, weight_multiplier)
    FIELD_PRIORS = {
        "Customer": {
            "email": {"m": 0.98, "u": 0.001, "jw_threshold": 0.88, "weight": 6.5},
            "phone": {"m": 0.95, "u": 0.005, "jw_threshold": 0.90, "weight": 5.0},
            "name": {"m": 0.92, "u": 0.02, "jw_threshold": 0.82, "weight": 4.5},
            "address": {"m": 0.85, "u": 0.01, "jw_threshold": 0.78, "weight": 3.5},
        },
        "Product": {
            "sku": {"m": 0.99, "u": 0.0005, "jw_threshold": 0.92, "weight": 7.0},
            "name": {"m": 0.90, "u": 0.03, "jw_threshold": 0.80, "weight": 5.0},
            "category": {"m": 0.80, "u": 0.15, "jw_threshold": 0.85, "weight": 2.0},
            "price": {"m": 0.85, "u": 0.10, "jw_threshold": 0.95, "weight": 2.5},
        },
        "Supplier": {
            "email": {"m": 0.98, "u": 0.002, "jw_threshold": 0.88, "weight": 6.5},
            "phone": {"m": 0.95, "u": 0.005, "jw_threshold": 0.90, "weight": 5.0},
            "name": {"m": 0.94, "u": 0.015, "jw_threshold": 0.82, "weight": 5.5},
            "address": {"m": 0.85, "u": 0.01, "jw_threshold": 0.78, "weight": 3.0},
        }
    }

    # Classification thresholds
    UPPER_MATCH_THRESHOLD = 9.0     # W >= 9.0: Definite Match
    LOWER_NON_MATCH_THRESHOLD = 2.0 # W < 2.0: Non-Match; Between: Possible Match (Human Review)

    @classmethod
    def get_field_weights(cls, record_type: str, field_name: str) -> Tuple[float, float]:
        """Calculates Fellegi-Sunter log2 agreement and disagreement weights."""
        type_priors = cls.FIELD_PRIORS.get(record_type, cls.FIELD_PRIORS["Customer"])
        priors = type_priors.get(field_name, {"m": 0.85, "u": 0.05, "weight": 3.0})
        m = priors["m"]
        u = priors["u"]

        w_agree = math.log2(m / u)
        w_disagree = math.log2((1.0 - m) / (1.0 - u))
        return w_agree, w_disagree

    @classmethod
    def compare_field(cls, record_type: str, field_name: str, val_a: Any, val_b: Any) -> Dict[str, Any]:
        """Compares values of a single field using typo-tolerant similarity and returns weights."""
        if val_a is None or val_b is None:
            return {
                "field": field_name,
                "status": "MISSING",
                "jaro_winkler": 0.0,
                "cosine": 0.0,
                "weight": 0.0,
                "agreement": False
            }

        str_a, str_b = str(val_a).strip(), str(val_b).strip()
        if not str_a or not str_b:
            return {
                "field": field_name,
                "status": "EMPTY",
                "jaro_winkler": 0.0,
                "cosine": 0.0,
                "weight": 0.0,
                "agreement": False
            }

        jw_sim = jaro_winkler_similarity(str_a, str_b)
        cos_sim = cosine_similarity_ngrams(str_a, str_b, n=3)

        type_priors = cls.FIELD_PRIORS.get(record_type, cls.FIELD_PRIORS["Customer"])
        config = type_priors.get(field_name, {"jw_threshold": 0.85, "m": 0.85, "u": 0.05})
        threshold = config.get("jw_threshold", 0.85)

        w_agree, w_disagree = cls.get_field_weights(record_type, field_name)

        # Graduated soft-weighting for typo tolerance
        if jw_sim >= threshold or cos_sim >= threshold:
            # Full agreement
            weight = w_agree * min(1.0, max(jw_sim, cos_sim))
            agreement = True
        elif max(jw_sim, cos_sim) >= (threshold - 0.15):
            # Partial agreement (typo tolerance zone)
            weight = w_agree * 0.4
            agreement = True
        else:
            # Disagreement
            weight = w_disagree
            agreement = False

        return {
            "field": field_name,
            "status": "COMPARED",
            "val_a": str_a,
            "val_b": str_b,
            "jaro_winkler": round(jw_sim, 4),
            "cosine": round(cos_sim, 4),
            "weight": round(weight, 3),
            "agreement": agreement
        }

    @classmethod
    def evaluate_pair(cls, record_a: Dict[str, Any], record_b: Dict[str, Any], record_type: str = "Customer") -> Dict[str, Any]:
        """
        Evaluates a candidate record pair using the Fellegi-Sunter linkage framework.
        Returns total weight, classification (DEFINITE_MATCH, POSSIBLE_MATCH, NON_MATCH),
        and detailed field-by-field diagnostic metrics.
        """
        type_priors = cls.FIELD_PRIORS.get(record_type, cls.FIELD_PRIORS["Customer"])
        total_weight = 0.0
        field_evaluations = {}
        agreed_fields = []
        disagreed_fields = []

        all_fields = list(type_priors.keys())
        for f in all_fields:
            val_a = record_a.get(f)
            val_b = record_b.get(f)
            cmp_res = cls.compare_field(record_type, f, val_a, val_b)
            field_evaluations[f] = cmp_res
            total_weight += cmp_res["weight"]

            if cmp_res["agreement"]:
                agreed_fields.append(f)
            elif cmp_res["status"] == "COMPARED":
                disagreed_fields.append(f)

        # Overall similarity aggregations
        jw_scores = [v["jaro_winkler"] for v in field_evaluations.values() if v["status"] == "COMPARED"]
        cos_scores = [v["cosine"] for v in field_evaluations.values() if v["status"] == "COMPARED"]
        avg_jw = sum(jw_scores) / len(jw_scores) if jw_scores else 0.0
        avg_cos = sum(cos_scores) / len(cos_scores) if cos_scores else 0.0

        # Classification decision based on Fellegi-Sunter weight
        if total_weight >= cls.UPPER_MATCH_THRESHOLD:
            classification = "DEFINITE_MATCH"
            action = "AUTO_LINK"
            confidence = min(99.9, max(85.0, 75.0 + (total_weight * 1.5)))
        elif total_weight >= cls.LOWER_NON_MATCH_THRESHOLD:
            classification = "POSSIBLE_MATCH"
            action = "MANUAL_REVIEW"
            confidence = min(84.0, max(50.0, 40.0 + (total_weight * 2.5)))
        else:
            classification = "NON_MATCH"
            action = "DISTINCT_ENTITY"
            confidence = max(5.0, 100.0 - abs(total_weight) * 10)

        return {
            "record_type": record_type,
            "fellegi_sunter_weight": round(total_weight, 3),
            "classification": classification,
            "action": action,
            "confidence_score": round(confidence, 1),
            "average_jaro_winkler": round(avg_jw, 4),
            "average_cosine": round(avg_cos, 4),
            "agreed_fields": agreed_fields,
            "disagreed_fields": disagreed_fields,
            "field_details": field_evaluations
        }


# =====================================================================
# 3. Probabilistic Linkage Ingestion & Clustering Manager
# =====================================================================

class ProbabilisticLinkageEngine:
    """High-level service for executing phonetic blocking, linkage clustering, and persistence."""

    @staticmethod
    def block_and_link(records: List[Dict[str, Any]], record_type: str = "Customer") -> List[Dict[str, Any]]:
        """
        Uses Soundex phonetic blocking on names/SKUs to form candidate pairs,
        then scores each candidate pair using the Fellegi-Sunter model.
        """
        # 1. Blocking pass: partition records into Soundex blocks
        blocks: Dict[str, List[Dict[str, Any]]] = {}
        for rec in records:
            name_val = rec.get("name") or rec.get("sku") or rec.get("business_identifier") or ""
            blk_key = soundex(str(name_val))
            blocks.setdefault(blk_key, []).append(rec)

        # 2. Pairwise comparison within blocks + cross-source validation
        candidate_pairs = []
        seen_pairs = set()

        for blk_key, block_records in blocks.items():
            n = len(block_records)
            for i in range(n):
                for j in range(i + 1, n):
                    rec_a = block_records[i]
                    rec_b = block_records[j]

                    id_a = str(rec_a.get("id") or rec_a.get("business_identifier") or i)
                    id_b = str(rec_b.get("id") or rec_b.get("business_identifier") or j)
                    pair_key = tuple(sorted([id_a, id_b]))
                    if pair_key in seen_pairs:
                        continue
                    seen_pairs.add(pair_key)

                    eval_res = FellegiSunterModel.evaluate_pair(rec_a, rec_b, record_type)
                    eval_res["source_a"] = rec_a.get("source_system", "Unknown")
                    eval_res["source_a_id"] = id_a
                    eval_res["source_b"] = rec_b.get("source_system", "Unknown")
                    eval_res["source_b_id"] = id_b
                    eval_res["record_a_name"] = rec_a.get("name")
                    eval_res["record_b_name"] = rec_b.get("name")
                    candidate_pairs.append(eval_res)

        return candidate_pairs

    @staticmethod
    def run_probabilistic_benchmark() -> Dict[str, Any]:
        """
        Tests the Fellegi-Sunter model against typo-injected real-world pairs.
        Demonstrates typo tolerance (e.g. spelling mistakes, phonetic variations, transposed characters).
        """
        test_cases = [
            {
                "case": "Phonetic Name Variation + Slight Email Typo",
                "record_a": {"name": "Jonathon Smith", "email": "jsmith@example.com", "phone": "5551234567", "address": "100 Market St"},
                "record_b": {"name": "Johnathan Smyth", "email": "jsmith@example.co", "phone": "5551234567", "address": "100 Market Street"},
                "expected": "DEFINITE_MATCH"
            },
            {
                "case": "Address Transposition & Abbreviation",
                "record_a": {"name": "Catherine Davis", "email": "cdavis@gmail.com", "phone": "4159876543", "address": "742 Evergreen Terrace Apt 2"},
                "record_b": {"name": "Kathryn Davis", "email": "cdavis@gmail.com", "phone": "4159876543", "address": "742 Evergreen Terr #2"},
                "expected": "DEFINITE_MATCH"
            },
            {
                "case": "Marginal Match (Different Phone & Address, Same Name)",
                "record_a": {"name": "Robert Miller", "email": "rmiller1@corp.com", "phone": "2125550100", "address": "12 Broadway NYC"},
                "record_b": {"name": "Robert Miller", "email": "rmiller99@yahoo.com", "phone": "3125550999", "address": "400 Michigan Ave Chicago"},
                "expected": "POSSIBLE_MATCH"
            },
            {
                "case": "Complete Disagreement (Distinct People)",
                "record_a": {"name": "Alice Cooper", "email": "alice@rock.com", "phone": "8001112222", "address": "1 Beverly Hills"},
                "record_b": {"name": "David Bowie", "email": "david@stardust.org", "phone": "8009998888", "address": "50 London Wall"},
                "expected": "NON_MATCH"
            }
        ]

        results = []
        correct = 0
        for tc in test_cases:
            res = FellegiSunterModel.evaluate_pair(tc["record_a"], tc["record_b"], "Customer")
            is_correct = res["classification"] == tc["expected"]
            if is_correct:
                correct += 1
            results.append({
                "case_name": tc["case"],
                "fellegi_sunter_weight": res["fellegi_sunter_weight"],
                "average_jaro_winkler": res["average_jaro_winkler"],
                "average_cosine": res["average_cosine"],
                "classification": res["classification"],
                "expected": tc["expected"],
                "is_correct": is_correct
            })

        return {
            "total_tests": len(test_cases),
            "passed": correct,
            "accuracy_pct": round((correct / len(test_cases)) * 100.0, 1),
            "benchmark_results": results
        }
