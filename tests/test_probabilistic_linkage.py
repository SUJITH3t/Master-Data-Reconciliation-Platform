"""
Unit and Integration Tests for Probabilistic Record Linkage and Fellegi-Sunter Methodology.
"""

import pytest
from engine.probabilistic_linkage import (
    soundex,
    jaro_similarity,
    jaro_winkler_similarity,
    cosine_similarity_ngrams,
    levenshtein_distance,
    FellegiSunterModel,
    ProbabilisticLinkageEngine
)


def test_soundex_phonetic_blocking():
    """Verify Soundex correctly groups phonetic variants for candidate blocking."""
    code1 = soundex("Smith")
    code2 = soundex("Smyth")
    code3 = soundex("Smithe")
    assert code1 == code2 == code3 == "S530"

    # Distinct name should have different code
    assert soundex("Johnson") != code1


def test_jaro_winkler_similarity_with_typos():
    """Verify Jaro-Winkler handles typographical errors with prefix weighting."""
    # Identical
    assert jaro_winkler_similarity("Jonathan", "Jonathan") == 1.0

    # Typo with shared prefix
    sim = jaro_winkler_similarity("Jonathon", "Jonathan")
    assert sim >= 0.90

    # Phonetic spelling difference
    sim_ph = jaro_winkler_similarity("Catherine", "Katherine")
    assert sim_ph >= 0.80

    # Distinct strings
    assert jaro_winkler_similarity("Apple", "Zebra") < 0.50


def test_cosine_similarity_ngrams_address():
    """Verify N-gram cosine similarity matches addresses with abbreviations."""
    addr1 = "100 Market Street Apt 4B"
    addr2 = "100 Market St #4B"
    cos_sim = cosine_similarity_ngrams(addr1, addr2, n=3)
    assert cos_sim >= 0.65


def test_fellegi_sunter_definite_match():
    """Verify high-agreement customer records classify as DEFINITE_MATCH."""
    rec_a = {
        "name": "Jonathon Smith",
        "email": "jsmith@example.com",
        "phone": "5551234567",
        "address": "100 Market St"
    }
    rec_b = {
        "name": "Johnathan Smyth",
        "email": "jsmith@example.co",
        "phone": "5551234567",
        "address": "100 Market Street"
    }
    eval_res = FellegiSunterModel.evaluate_pair(rec_a, rec_b, "Customer")
    assert eval_res["classification"] == "DEFINITE_MATCH"
    assert eval_res["fellegi_sunter_weight"] >= FellegiSunterModel.UPPER_MATCH_THRESHOLD
    assert eval_res["action"] == "AUTO_LINK"


def test_fellegi_sunter_marginal_possible_match():
    """Verify marginal ties classify as POSSIBLE_MATCH for human review."""
    rec_a = {
        "name": "Robert Miller",
        "email": "rmiller1@corp.com",
        "phone": "2125550100",
        "address": "12 Broadway NYC"
    }
    rec_b = {
        "name": "Robert Miller",
        "email": "rmiller99@yahoo.com",
        "phone": "3125550999",
        "address": "400 Michigan Ave Chicago"
    }
    eval_res = FellegiSunterModel.evaluate_pair(rec_a, rec_b, "Customer")
    assert eval_res["classification"] == "POSSIBLE_MATCH"
    assert eval_res["action"] == "MANUAL_REVIEW"


def test_fellegi_sunter_non_match():
    """Verify distinct individuals classify as NON_MATCH with negative weight."""
    rec_a = {"name": "Alice Cooper", "email": "alice@rock.com", "phone": "8001112222", "address": "1 Beverly Hills"}
    rec_b = {"name": "David Bowie", "email": "david@stardust.org", "phone": "8009998888", "address": "50 London Wall"}
    eval_res = FellegiSunterModel.evaluate_pair(rec_a, rec_b, "Customer")
    assert eval_res["classification"] == "NON_MATCH"
    assert eval_res["fellegi_sunter_weight"] < FellegiSunterModel.LOWER_NON_MATCH_THRESHOLD


def test_probabilistic_benchmark_suite():
    """Verify 100% benchmark accuracy across all test scenarios."""
    bench = ProbabilisticLinkageEngine.run_probabilistic_benchmark()
    assert bench["accuracy_pct"] == 100.0
    assert bench["passed"] == bench["total_tests"]
