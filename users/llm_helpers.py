import json

import openai
from openai import OpenAI

from dealflow_automator.settings import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

client = OpenAI()


def get_bulk_product_tiers_and_descriptions(companies):
    """
    companies: List of dicts, each with 'description' and 'website'
    Returns:
        - List of product tiers (ints or None)
        - List of 2-word descriptions (str)
    """
    prompt = f"""
You are an analyst evaluating companies based on the following business descriptions and websites.

For each company:
- Use the description and website to determine the business model.
- Return a tier (1-4) based on the rules below.
- Generate a short, lowercase 2–3 word description of the business.

### Tiering Rules:
- Tier 1: Vertical/Industrial B2B software, B2B software + hardware/services.
- Tier 2: Horizontal B2B software.
- Tier 4: Custom dev shop, system integrator, B2C, non-tech services.
- Tier 3: Only if ambiguous between Tier 2 and Tier 4.

### Output format:
Return a JSON list of objects like this:
[
  {{
    "tier": 1,
    "description": "health data analytics"
  }},
  ...
]

### Companies:
{json.dumps(companies[:15], indent=2)}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()

        # Try to parse the JSON response
        try:
            parsed = json.loads(content)
            tiers = [item.get("tier") for item in parsed]
            descriptions = [item.get("description", "") for item in parsed]
            return tiers, descriptions
        except json.JSONDecodeError:
            print("Error decoding GPT response as JSON:", content)
            return [None] * len(companies), [""] * len(companies)

    except Exception as e:
        print("OpenAI Error (bulk):", e)
        return [None] * len(companies), [""] * len(companies)
