import io
import chardet

import pandas as pd
from celery import shared_task
from django.contrib.auth.models import User

from .models import UserConfiguration
from .utilities import generate_descriptions_and_tiers_with_progress, clear_progress


@shared_task
def process_file_task(file_data, filename, user_id):
    user = User.objects.get(id=user_id)
    config = UserConfiguration.objects.get(user=user).configuration_json

    # --- Read file into DataFrame ---
    if filename.endswith(".csv"):
        # Detect encoding
        result = chardet.detect(file_data)
        encoding = result["encoding"] or "utf-8"

        # Read CSV
        df = pd.read_csv(io.BytesIO(file_data), encoding=encoding)
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(file_data))
    else:
        raise ValueError("Unsupported file format")

    # --- Clean and convert data ---
    df = df[df["Company Name"].notna()].reset_index(drop=True)
    df["Founding Year"] = pd.to_numeric(df.get("Founding Year"), errors="coerce")
    df["Total Raised"] = pd.to_numeric(df.get("Total Raised"), errors="coerce")
    df["Employee Count"] = pd.to_numeric(df.get("Employee Count"), errors="coerce")

    # --- Tier logic ---
    def get_founding_tier(year):
        if pd.isna(year): return None
        year = int(year)
        for tier, max_year in config["founding_year"].items():
            if year <= int(max_year):
                return int(tier[-1])
        return 4

    def get_fundraise_tier(date_str):
        if pd.isna(date_str): return 3
        try:
            year = pd.to_datetime(date_str).year
            for tier, val in config["fundraiser_year"].items():
                if year <= int(val):
                    return int(tier[-1])
        except:
            pass
        return 3

    def get_total_raised_tier(row):
        raised = row["Total Raised"]
        owner = row["Ownership"]
        if pd.isna(raised) or pd.isna(owner):
            return None
        owner_group = owner if owner in config["total_raised"]["tier_1"] else "Others"
        for tier in ["tier_1", "tier_1_extra", "tier_2", "tier_3"]:
            limit = config["total_raised"].get(tier, {}).get(owner_group)
            if limit is not None:
                try:
                    if float(raised) <= float(limit):
                        return int(tier[-1])
                except:
                    continue
        return 4

    def get_fte_tier(row):
        fte = row["Employee Count"]
        ownership = row["Ownership"]
        if pd.isna(fte) or pd.isna(ownership): return None
        try:
            fte = int(fte)
            for tier, rule in config["FTE_Count"].items():
                limits = rule.get(ownership)
                if limits and limits.get("min") <= fte <= limits.get("max"):
                    return int(tier[-1])
        except:
            return None
        return 4

    # --- Apply tiers ---
    df["country_tier"] = df["Country"].map(config.get("country", {}))
    df["ownership_tier"] = df["Ownership"].map(config.get("Ownership", {}))
    df["founding_tier"] = df["Founding Year"].apply(get_founding_tier)
    df["fundraise_tier"] = df["Date of Most Recent Investment"].apply(get_fundraise_tier)
    df["raised_tier"] = df.apply(get_total_raised_tier, axis=1)
    df["fte_tier"] = df.apply(get_fte_tier, axis=1)

    df["Pre-Product Tier"] = df[[
        "country_tier", "ownership_tier", "founding_tier",
        "fundraise_tier", "raised_tier", "fte_tier"
    ]].max(axis=1)

    # --- GPT-based description + tiering ---
    product_tiers, descriptions = generate_descriptions_and_tiers_with_progress(df, user.id)
    df["Product Tier - CHAT GPT"] = pd.Series(pd.to_numeric(product_tiers, errors="coerce")).fillna(0)
    df["2 Word Description"] = descriptions

    # --- Final processing ---
    df["Order"] = df["Pre-Product Tier"].rank(method="min", ascending=True).astype(int)
    df["Post Tier"] = df[["Pre-Product Tier", "Product Tier - CHAT GPT"]].max(axis=1)
    df["Index"] = df.index + 1
    df["Post_Order"] = df["Post Tier"] * 10000 - df["Index"]
    df["Post Rank"] = df["Post_Order"].rank(method="min", ascending=True).astype(int)
    df["Tier"] = df["Post Tier"]

    # --- Clean output ---
    final_columns = [
        "Post Rank", "Tier", "Company Name", "Informal Name", "Founding Year", "Country",
        "Website", "Description", "Employee Count", "Ownership", "Total Raised",
        "Date of Most Recent Investment", "Executive Title", "Executive First Name",
        "Executive Last Name", "Executive Email", "Investors", "2 Word Description"
    ]
    processed_df = df[[col for col in final_columns if col in df.columns]].copy()
    processed_df.rename(columns={
        "Employee Count": "Count",
        "Company Name": "Name"
    }, inplace=True)

    df["2 Word Description - CHAT GPT"] = df["2 Word Description"]
    df["Include"] = ""
    action_columns = [
        "Pre-Product Tier", "Order", "Post Tier", "Post_Order", "Post Rank", "Index",
        "Include", "Company Name", "Website", "Description", "Employee Count",
        "Product Tier - CHAT GPT", "2 Word Description - CHAT GPT"
    ]
    action_df = df[[col for col in action_columns if col in df.columns]].copy()

    # --- Convert to CSV strings ---
    processed_csv = io.StringIO()
    action_csv = io.StringIO()
    processed_df.to_csv(processed_csv, index=False)
    action_df.to_csv(action_csv, index=False)

    clear_progress(user.id)

    return {
        "processed_csv": processed_csv.getvalue(),
        "action_csv": action_csv.getvalue(),
    }