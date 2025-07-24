import pandas as pd
from django.core.cache import cache

from users.llm_helpers import get_product_tier, get_two_word_description


def save_progress(user_id, current, total):
    """
    Saves the current progress of a task for a user in Django's cache system.

    Args:
        user_id (int): The ID of the user.
        current (int): The current step completed.
        total (int): The total number of steps.

    Cache:
        Stores a dictionary with keys: 'current', 'total', and 'percent'.
        Cached under the key 'progress_<user_id>'.
        Expires in 1 hour (3600 seconds).
    """
    percent = round((current / total) * 100, 2) if total else 0
    cache.set(f"{user_id}_progress", {"current": current, "total": total, "percent": percent}, timeout=3600)


def clear_progress(user_id):
    """
    Clears the progress data for a user from Django's cache.

    Args:
        user_id (int): The ID of the user.

    Cache:
        Deletes the cached value under 'progress_<user_id>'.
    """
    cache.delete(f"progress_{user_id}")


def generate_descriptions_and_tiers_with_progress(df, user_id):
    """
    Processes each row in the given DataFrame to generate product tiers and two-word descriptions
    using LLM-based helper functions. Tracks and saves progress for each step.

    For each row, this function:
    - Calls `get_product_tier()` to determine a tier based on the description and website.
    - Calls `get_two_word_description()` to generate a brief business description.
    - Saves progress after each step to allow real-time progress tracking.

    Args:
        df (pd.DataFrame): The input DataFrame containing company data.
        user_id (int): ID of the user for whom progress is being tracked.

    Returns:
        tuple: A tuple of two lists:
            - product_tiers (list[int]): List of generated product tier values (1–4 or 0 on failure).
            - descriptions (list[str]): List of generated 2–3 word business descriptions.
    """
    total_rows = len(df)
    total_steps = total_rows * 2
    current = 0

    product_tiers = []
    descriptions = []

    for _, row in df.iterrows():
        # Product Tier
        try:
            product_tier = get_product_tier(row.get("Description", ""), row.get("Website", ""))
        except:
            product_tier = 0
        product_tiers.append(product_tier)
        current += 1
        save_progress(user_id, current, total_steps)

        # Description
        try:
            desc = get_two_word_description(row.get("Description", ""), row.get("Website", ""))
        except:
            desc = ""
        descriptions.append(desc)
        current += 1
        save_progress(user_id, current, total_steps)

    return product_tiers, descriptions
