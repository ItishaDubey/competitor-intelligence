import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


class IntelligenceEngine:

    def __init__(self):

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"⚠️ OpenAI init failed: {e}")
                self.client = None
        else:
            print("⚠️ OPENAI_API_KEY not found — running in TEST MODE.")


    # =====================================================
    # STRATEGIC INSIGHT GENERATOR
    # =====================================================
    def generate(self, baseline, diff, competitor_name):

        matched = diff.get("matched", [])
        missing = diff.get("missing", [])

        prompt = f"""
You are a senior competitive pricing strategist.

Competitor: {competitor_name}

Matched Products Count: {len(matched)}
Missing Products Count: {len(missing)}

Provide:
1. Pricing risks
2. Opportunities
3. Recommendations to increase sales
"""

        # ------------------------------------------------
        # REAL AI MODE
        # ------------------------------------------------
        if self.client:
            try:
                response = self.client.responses.create(
                    model="gpt-4o-mini",
                    input=prompt
                )
                return response.output_text

            except Exception as e:
                print(f"⚠️ OpenAI call failed, switching to TEST MODE: {e}")

        # ------------------------------------------------
        # TEST MODE (OFFLINE FALLBACK)
        # ------------------------------------------------
        return f"""
[TEST INSIGHTS — OFFLINE MODE]

Competitor: {competitor_name}

Matched Products Count: {len(matched)}
Missing Products Count: {len(missing)}

Strategic Suggestions:
- Monitor competitor pricing changes.
- Add missing SKUs to increase catalog coverage.
- Improve product content to boost conversions.
"""
