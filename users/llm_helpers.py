import openai
from openai import OpenAI

from dealflow_automator.settings import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

client = OpenAI()


def get_product_tier(description, website):
    prompt = f"""
You are an analyst at a private equity firm evaluating companies based on their business models.

Input:
- Website: {website}
- Description: {description}

Instructions:
1. Base your judgment ONLY on the given Description and Website text. 
   Do not invent details and do not assume you can browse the website.
2. If the description is empty or vague, default to Tier 4.
3. Follow this decision process step-by-step:

Step 1: Does the company clearly sell software as its main offering?
    - If NO → Tier 4
    - If YES → go to Step 2

Step 2: Is the software designed for a specific industry (healthcare, construction, manufacturing, logistics, etc.)?
    - If YES → Tier 1
    - If NO → go to Step 3

Step 3: Is the software general-purpose and usable across multiple industries (e.g., CRM, HR, generic project management)?
    - If YES → Tier 2
    - If NO → Tier 4

Tier definitions:
- Tier 1: Industry-specific B2B software; may include software + hardware or software + services (where software is the primary value)
- Tier 2: Horizontal/general-purpose B2B software
- Tier 4: Anything that is not B2B software

Output:
- Return only a single number: 1, 2, or 4
- No extra text, no explanations
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
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
