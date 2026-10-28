"""
Mathematical Reviewer-Capacity and Queuing Theory Analysis Engine.
Implements the Erlang-C (M/M/c) multi-server queuing model to analyze human steward
workload, queue latency, SLA compliance probability, and staffing capacity requirements.
"""

import math
from typing import Any, Dict, List, Tuple


class CapacityAnalysisEngine:
    """
    Mathematical Erlang-C (M/M/c) Queuing Model for Master Data Governance Reviewers.
    Calculates staffing requirements, server utilization, queue wait times, and SLA compliance.
    """

    @staticmethod
    def erlang_c_probability(c: int, traffic_intensity_a: float) -> float:
        """
        Calculates Erlang-C probability of a case experiencing queue delay:
          P_w = (A^c / c!) * (c / (c - A)) / [ sum_{k=0}^{c-1} (A^k / k!) + (A^c / c!) * (c / (c - A)) ]
        """
        if c <= traffic_intensity_a:
            return 1.0  # System is unstable (queue grows infinitely)

        # Calculate sum_{k=0}^{c-1} (A^k / k!) in log space to prevent numeric overflow
        sum_terms = 0.0
        current_term = 1.0
        for k in range(c):
            sum_terms += current_term
            current_term *= (traffic_intensity_a / (k + 1))

        # C-term: (A^c / c!) * (c / (c - A))
        c_term = current_term * (c / (c - traffic_intensity_a))
        p0 = 1.0 / (sum_terms + c_term)
        pw = c_term * p0
        return min(1.0, max(0.0, pw))

    @classmethod
    def evaluate_capacity(
        cls,
        daily_ingestion_volume: int = 50000,
        manual_review_rate: float = 0.10,
        operating_hours_per_day: float = 8.0,
        average_handle_time_sec: float = 120.0,
        target_sla_minutes: float = 10.0,
        target_sla_compliance_pct: float = 95.0,
        shrinkage_pct: float = 15.0,
        max_cases_per_reviewer_hour: int = 25
    ) -> Dict[str, Any]:
        """
        Evaluates reviewer staffing, utilization, latency, and SLA achievement.
        """
        # Daily and hourly review volume
        total_review_cases = daily_ingestion_volume * manual_review_rate
        arrival_rate_per_hour = total_review_cases / operating_hours_per_day
        arrival_rate_per_sec = arrival_rate_per_hour / 3600.0

        # Reviewer service capacity
        service_rate_per_reviewer_hour = 3600.0 / average_handle_time_sec
        service_rate_per_sec = 1.0 / average_handle_time_sec

        # Offered traffic intensity (A = lambda / mu) in Erlangs
        traffic_intensity_a = arrival_rate_per_sec / service_rate_per_sec
        min_headcount = math.floor(traffic_intensity_a) + 1

        target_sla_sec = target_sla_minutes * 60.0

        # Find optimal active reviewers meeting SLA target
        c = min_headcount
        best_c = c
        sla_achieved = 0.0
        avg_wait_sec = 0.0

        for candidate_c in range(min_headcount, min_headcount + 50):
            pw = cls.erlang_c_probability(candidate_c, traffic_intensity_a)
            denominator = (candidate_c * service_rate_per_sec) - arrival_rate_per_sec

            if denominator > 0:
                wait_sec = pw / denominator
                # P(Wait <= SLA) = 1 - pw * exp(-denominator * SLA)
                prob_sla = 1.0 - (pw * math.exp(-denominator * target_sla_sec))
                prob_sla_pct = prob_sla * 100.0

                if prob_sla_pct >= target_sla_compliance_pct:
                    best_c = candidate_c
                    sla_achieved = prob_sla_pct
                    avg_wait_sec = wait_sec
                    break
                best_c = candidate_c
                sla_achieved = prob_sla_pct
                avg_wait_sec = wait_sec

        # Utilization rho = A / c
        utilization_pct = (traffic_intensity_a / best_c) * 100.0

        # Gross FTE factoring in off-queue shrinkage (breaks, PTO, training)
        shrinkage_multiplier = 1.0 / (1.0 - (shrinkage_pct / 100.0))
        required_gross_fte = math.ceil(best_c * shrinkage_multiplier)

        # Workload per specialist per hour
        actual_cases_per_specialist_hr = arrival_rate_per_hour / best_c
        fatigue_risk = "Low" if actual_cases_per_specialist_hr <= max_cases_per_reviewer_hour * 0.75 else (
            "Moderate" if actual_cases_per_specialist_hr <= max_cases_per_reviewer_hour else "High (Cognitive Burnout Risk)"
        )

        return {
            "daily_ingestion_volume": daily_ingestion_volume,
            "manual_review_rate_pct": manual_review_rate * 100.0,
            "daily_review_cases": int(total_review_cases),
            "arrival_rate_per_hour": round(arrival_rate_per_hour, 1),
            "average_handle_time_sec": average_handle_time_sec,
            "offered_load_erlangs": round(traffic_intensity_a, 2),
            "min_theoretical_servers": min_headcount,
            "recommended_active_reviewers": best_c,
            "required_gross_fte": required_gross_fte,
            "utilization_pct": round(utilization_pct, 1),
            "avg_queue_wait_minutes": round(avg_wait_sec / 60.0, 2),
            "target_sla_minutes": target_sla_minutes,
            "sla_compliance_pct": round(sla_achieved, 1),
            "target_sla_compliance_pct": target_sla_compliance_pct,
            "cases_per_reviewer_hour": round(actual_cases_per_specialist_hr, 1),
            "fatigue_risk_level": fatigue_risk
        }

    @classmethod
    def generate_capacity_matrix(cls) -> List[Dict[str, Any]]:
        """Generates enterprise workload scaling matrix across volume tiers."""
        scenarios = [
            {"tier": "Pilot / Store Pilot", "volume": 10000, "mr_rate": 0.08, "aht": 90},
            {"tier": "Mid-Market Retail", "volume": 50000, "mr_rate": 0.10, "aht": 120},
            {"tier": "Large Enterprise HQ", "volume": 150000, "mr_rate": 0.10, "aht": 120},
            {"tier": "Peak Holiday Shopping", "volume": 500000, "mr_rate": 0.12, "aht": 150},
        ]
        results = []
        for s in scenarios:
            eval_res = cls.evaluate_capacity(
                daily_ingestion_volume=s["volume"],
                manual_review_rate=s["mr_rate"],
                average_handle_time_sec=s["aht"],
                target_sla_minutes=15.0
            )
            eval_res["tier"] = s["tier"]
            results.append(eval_res)
        return results
