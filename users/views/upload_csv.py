import io
import json
import os

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from llm_helpers import get_product_tier, get_two_word_description
from users.models import User
from users.models import UserConfiguration

# === Progress Tracking Helpers ===
PROGRESS_DIR = "/tmp/progress"  # Adjust as needed
os.makedirs(PROGRESS_DIR, exist_ok=True)


def get_progress_file_path(user_id):
    return os.path.join(PROGRESS_DIR, f"progress_{user_id}.json")


def save_progress(user_id, current, total):
    percent = round((current / total) * 100, 2)
    with open(get_progress_file_path(user_id), "w") as f:
        json.dump({"current": current, "total": total, "percent": percent}, f)


def clear_progress(user_id):
    path = get_progress_file_path(user_id)
    if os.path.exists(path):
        os.remove(path)


# === Combined Description & Tier Progress ===
def generate_descriptions_and_tiers_with_progress(df, user_id):
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


# === Main View ===
class UploadAndTierView(View):
    def get(self, request):
        return render(request, "upload_csv.html")

    def post(self, request):
        try:
            file = request.FILES["file"]
            filename = file.name.lower()

            user = User.objects.filter(is_superuser=True).first()
            if not user:
                return JsonResponse({"status": "error", "message": "Superuser not found"}, status=404)

            config = UserConfiguration.objects.get(user=user).configuration_json

            # Read the file
            if filename.endswith(".csv"):
                try:
                    file_data = file.read()
                    df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(io.BytesIO(file_data), encoding="latin1")
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
            else:
                return JsonResponse({"error": "Unsupported file format. Please upload .csv or .xlsx"}, status=400)

            df = df[df["Company Name"].notna()].reset_index(drop=True)
            df["Founding Year"] = pd.to_numeric(df.get("Founding Year"), errors="coerce")
            df["Total Raised"] = pd.to_numeric(df.get("Total Raised"), errors="coerce")
            df["Employee Count"] = pd.to_numeric(df.get("Employee Count"), errors="coerce")

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
                        if year <= int(val): return int(tier[-1])
                except:
                    pass
                return 3

            def get_total_raised_tier(row):
                raised = row["Total Raised"]
                owner = row["Ownership"]
                if pd.isna(raised) or pd.isna(owner): return None
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

            # Apply tiering logic
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

            # Run GPT-based functions with progress tracking
            product_tiers, descriptions = generate_descriptions_and_tiers_with_progress(df, user.id)

            df["Product Tier - CHAT GPT"] = pd.Series(pd.to_numeric(product_tiers, errors="coerce")).fillna(0)
            df["2 Word Description"] = descriptions

            df["Order"] = df["Pre-Product Tier"].rank(method="min", ascending=True).astype(int)
            df["Post Tier"] = df[["Pre-Product Tier", "Product Tier - CHAT GPT"]].max(axis=1)
            df["Index"] = df.index + 1
            df["Post_Order"] = df["Post Tier"] * 10000 - df["Index"]
            df["Post Rank"] = df["Post_Order"].rank(method="min", ascending=True).astype(int)
            df["Tier"] = df["Post Tier"]

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

            processed_csv = io.StringIO()
            action_csv = io.StringIO()
            processed_df.to_csv(processed_csv, index=False)
            action_df.to_csv(action_csv, index=False)

            clear_progress(user.id)

            return JsonResponse({
                "processed_csv": processed_csv.getvalue(),
                "action_csv": action_csv.getvalue(),
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# === Progress Polling Endpoint ===
def check_progress(request):
    user = User.objects.get()
    path = get_progress_file_path(user.id)
    if not os.path.exists(path):
        return JsonResponse({"current": 0, "total": 0, "percent": 0})
    with open(path, "r") as f:
        return JsonResponse(json.load(f))
