import numpy as np
import pandas as pd
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from users.models import UserConfiguration, User


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
            user_config = UserConfiguration.objects.get(user=user).configuration_json

            if filename.endswith(".csv"):
                df = pd.read_csv(file)
            elif filename.endswith(".xlsx") or filename.endswith(".xls"):
                df = pd.read_excel(file)
            else:
                return JsonResponse({"error": "Unsupported file format. Please upload .csv or .xlsx"}, status=400)

            transformed_df = self.apply_user_config_tiering(df, user_config)

            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = "attachment; filename=processed.csv"
            transformed_df.to_csv(response, index=False)
            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @staticmethod
    def apply_user_config_tiering(df: pd.DataFrame, config: dict) -> pd.DataFrame:
        df = df.copy()

        # ---- Country Tier ----
        country_map = config.get("country", {})
        df["Country Tier"] = df["Country"].map(lambda x: country_map.get(x) or country_map.get("All others"))

        # ---- Ownership Tier ----
        ownership_map = config.get("Ownership", {})
        df["Ownership Tier"] = df["Ownership"].map(lambda x: ownership_map.get(x))

        # ---- FTE Tier ----
        def get_fte_tier(row):
            ownership = row.get("Ownership")
            fte = row.get("Employee Count")
            if pd.isna(fte) or ownership is None:
                return np.nan
            for tier, type_dict in config.get("FTE_Count", {}).items():
                tier_num = int(tier.split("_")[1])
                props = type_dict.get(ownership)
                if not props:
                    continue
                min_ = props.get("min")
                max_ = props.get("max")
                if (min_ is None or fte >= min_) and (max_ is None or fte <= max_):
                    return tier_num
            return np.nan

        df["FTE Tier"] = df.apply(get_fte_tier, axis=1)

        # ---- Founding Year Tier ----
        def get_founding_year_tier(row):
            year = row.get("Founding Year")
            if pd.isna(year):
                return np.nan
            for tier, max_year in config.get("founding_year", {}).items():
                if pd.notna(max_year) and int(year) <= int(max_year):
                    return int(tier.split("_")[1])
            return np.nan

        df["Founding Year Tier"] = df.apply(get_founding_year_tier, axis=1)

        # ---- Fundraiser Year Tier ----
        def get_fundraiser_year_tier(row):
            year = row.get("Fundraiser Year")
            if pd.isna(year):
                return np.nan
            for tier, max_val in config.get("fundraiser_year", {}).items():
                if pd.notna(max_val) and int(year) <= int(max_val):
                    return int(tier.split("_")[1])
            return np.nan

        df["Fundraiser Year Tier"] = df.apply(get_fundraiser_year_tier, axis=1)

        # ---- Total Raised Tier ----
        def get_total_raised_tier(row):
            raised = row.get("Total Raised")
            if pd.isna(raised):
                return np.nan
            ownership_key = str(row.get("Ownership", "Others")).lower().replace(" ", "_")
            for tier, rule in config.get("total_raised", {}).items():
                tier_num = int(tier.split("_")[1])
                for key, max_val in rule.items():
                    if key.lower() in ownership_key and raised <= max_val:
                        return tier_num
            return np.nan

        df["Total Raised Tier"] = df.apply(get_total_raised_tier, axis=1)

        # ---- Final Tier (lowest number = highest priority) ----
        df["Final Tier"] = df[[
            "Country Tier",
            "Ownership Tier",
            "FTE Tier",
            "Founding Year Tier",
            "Fundraiser Year Tier",
            "Total Raised Tier"
        ]].min(axis=1, skipna=True)

        return df
