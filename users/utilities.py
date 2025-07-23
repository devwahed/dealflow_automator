import pandas as pd
from django.core.cache import cache

from users.llm_helpers import get_bulk_product_tiers_and_descriptions


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
    print(f"Progress saved: {current}/{total} ({percent}%)")
    cache.set(f"progress_{user_id}", {"current": current, "total": total, "percent": percent}, timeout=3600)


def clear_progress(user_id):
    """
    Clears the progress data for a user from Django's cache.

    Args:
        user_id (int): The ID of the user.

    Cache:
        Deletes the cached value under 'progress_<user_id>'.
    """
    cache.delete(f"progress_{user_id}")


def generate_descriptions_and_tiers_with_progress(df, user_id, batch_size=10):
    """
    Uses bulk GPT calls for better speed while tracking progress after each row.
    """
    total_rows = len(df)
    total_steps = total_rows * 2  # One step for tier, one for description
    current = 0

    product_tiers = []
    descriptions = []

    companies = [
        {
            "description": str(row.get("Description", "")),
            "website": str(row.get("Website", ""))
        }
        for _, row in df.iterrows()
    ]

    for i in range(0, len(companies), batch_size):
        batch = companies[i:i + batch_size]

        # Get results from GPT
        batch_tiers, batch_descs = get_bulk_product_tiers_and_descriptions(batch)

        # Add to final result
        for tier, desc in zip(batch_tiers, batch_descs):
            product_tiers.append(tier if tier in [1, 2, 3, 4] else 0)
            descriptions.append(desc)

            # Save progress twice: one for tier, one for description
            current += 1
            save_progress(user_id, current, total_steps)
            current += 1
            save_progress(user_id, current, total_steps)

    return product_tiers, descriptions
