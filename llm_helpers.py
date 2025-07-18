import openai
from openai import OpenAI

from dealflow_automator.settings import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

client = OpenAI()


def get_product_tier(description, website):
    prompt = f"""
You are an analyst at a private equity firm evaluating companies based on their business models.
For each company, use the following fields:
- Website: {website}
- Description: {description}
Your task:
1. Use the provided Description and Website fields to understand the business model.
2. Do not fabricate information. You are not able to visit or browse the website independently.
3. Confirm if the Website string supports or aligns with the Description.
4. Determine whether the business offers software, services, hardware, or a combination.

Then assign a **Tier from 1 to 4** using the rules below:

### Tiering Criteria:
- Return 1 if the company sells:
  - Vertical B2B software
  - Industrial B2B software
  - B2B software + hardware
  - B2B software + services
- Return 2 if the company sells:
  - Horizontal B2B software
- Return 4 if the company is:
  - A custom software development service
  - A system integrator
  - A non-tech or non-recurring services business
  - A B2C software company
- Return 3 only if it is truly ambiguous between Tier 2 and Tier 4.

### Output Instructions:
- Return only the number: 1, 2, 3, or 4
- Do not include any explanation, notes, or formatting.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip()
        return int(result) if result in {"1", "2", "3", "4"} else None
    except Exception as e:
        print("OpenAI Error (Product Tier):", e)
        return None


def get_two_word_description(description, website):
    prompt = f"""
For each company, use the following values:
- Website: {website}
- Description: {description}

1. Look at the description and website to figure out what the company does.
2. Return a short, specific 2–3 word description of the business in all lowercase with no punctuation.
3. Your response must fit into the sentence:
   "We've developed a thesis around [2-word description] and we've heard good things about your company..."

Only return the 2–3 word description. Do not include any other text or formatting.

For example, the output for https://lactanet.ca/ would be "herd management solutions"
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
        )
        result = response.choices[0].message.content.strip().lower()
        return result
    except Exception as e:
        print("OpenAI Error (2 Word Description):", e)
        return ""
