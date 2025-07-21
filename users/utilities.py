import json
import os

import pandas as pd

from users.llm_helpers import get_product_tier, get_two_word_description

PROGRESS_DIR = "/tmp/progress"
os.makedirs(PROGRESS_DIR, exist_ok=True)


def get_progress_file_path(user_id):
    """
    Returns the full path to the progress file for a given user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        str: Path to the progress JSON file.
    """
    return os.path.join(PROGRESS_DIR, f"progress_{user_id}.json")


def save_progress(user_id, current, total):
    """
    Saves the current progress of a task for a user.

    Args:
        user_id (int): The ID of the user.
        current (int): The current step completed.
        total (int): The total number of steps.

    Writes:
        A JSON file with keys: 'current', 'total', and 'percent'.
    """
    percent = round((current / total) * 100, 2)
    with open(get_progress_file_path(user_id), "w") as f:
        json.dump({"current": current, "total": total, "percent": percent}, f)


def clear_progress(user_id):
    """
    Deletes the progress file for a given user if it exists.

    Args:
       user_id (int): The ID of the user.
    """
    path = get_progress_file_path(user_id)
    if os.path.exists(path):
        os.remove(path)


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
    total_steps = total_rows * 2  # One for product_tier, one for description
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
