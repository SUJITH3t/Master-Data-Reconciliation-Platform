"""Optional Groq API Integration for Explanation Polishing."""

import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    @staticmethod
    def is_available() -> bool:
        """Check if Groq API key is present and configured."""
        key = os.environ.get("GROQ_API_KEY", "").strip()
        return bool(key and key != "your_groq_api_key_here")

    @staticmethod
    def polish_explanation(
        deterministic_explanation: str,
        entity_type: str,
        field_name: str,
        winner: Any,
        winning_source: Optional[str]
    ) -> str:
        """
        Enhance plain-English readability using Groq if available.
        NOTE: Groq NEVER decides the winner. Winner and evidence are fixed.
        """
        if not LLMService.is_available():
            return deterministic_explanation

        try:
            from groq import Groq
            client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            
            prompt = (
                f"You are a master data governance business assistant. "
                f"Rewrite this technical reconciliation explanation into concise, crystal-clear business English for an executive dashboard.\n\n"
                f"Entity: {entity_type}\n"
                f"Field: {field_name}\n"
                f"Selected Master Value: {winner}\n"
                f"Winning Source: {winning_source}\n"
                f"Decision Rationale: {deterministic_explanation}\n\n"
                f"Constraint: Retain exactly the factual decision and winning source. Do NOT change the facts. "
                f"Output only 1-2 business sentences."
            )

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You polish master data explanations into clean business language."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.2,
                max_tokens=150
            )
            refined = chat_completion.choices[0].message.content.strip()
            return refined if refined else deterministic_explanation
        except Exception:
            # Safe fallback if API error, rate limit, or invalid key occurs
            return deterministic_explanation
