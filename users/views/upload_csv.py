import pandas as pd
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import View

from users.models import User, UserConfiguration


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

            if filename.endswith(".csv"):
                df = pd.read_csv(file)
            elif filename.endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
            else:
                return JsonResponse({"error": "Unsupported file format. Please upload .csv or .xlsx"}, status=400)

            df = df[df["Company Name"].notna()].reset_index(drop=True)

            # Convert numeric columns safely
            df["Founding Year"] = pd.to_numeric(df.get("Founding Year"), errors="coerce")
            df["Total Raised"] = pd.to_numeric(df.get("Total Raised"), errors="coerce")
            df["Employee Count"] = pd.to_numeric(df.get("Employee Count"), errors="coerce")

            def get_founding_tier(year):
                if pd.isna(year):
                    return None
                year = int(year)
                for tier, max_year in config["founding_year"].items():
                    if year <= int(max_year):
                        return int(tier[-1])
                return 4

            def get_fundraise_tier(date_str):
                if pd.isna(date_str):
                    return 3
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
                if pd.isna(fte) or pd.isna(ownership):
                    return None
                try:
                    fte = int(fte)
                    for tier, rule in config["FTE_Count"].items():
                        limits = rule.get(ownership)
                        if limits and limits.get("min") <= fte <= limits.get("max"):
                            return int(tier[-1])
                except:
                    return None
                return 4

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

            if "Product Tier - CHAT GPT" in df.columns:
                df["Product Tier - CHAT GPT"] = pd.to_numeric(df["Product Tier - CHAT GPT"], errors="coerce").fillna(0)
            else:
                df["Product Tier - CHAT GPT"] = 0

            df["Order"] = df["Pre-Product Tier"].rank(method="min", ascending=True).astype(int)
            df["Post Tier"] = df[["Pre-Product Tier", "Product Tier - CHAT GPT"]].max(axis=1)
            df["Index"] = df.index + 1
            df["Post_Order"] = df["Post Tier"] * 10000 - df["Index"]
            df["Post Rank"] = df["Post_Order"].rank(method="min", ascending=True).astype(int)
            df["Tier"] = df["Post Tier"]

            def get_two_words(val):
                return " ".join(str(val).split()[:2]) if pd.notna(val) else ""

            df["2 Word Description"] = df["Company Name"].apply(get_two_words)

            final_columns = [
                "Post Rank", "Tier", "Company Name", "Informal Name", "Founding Year", "Country",
                "Website", "Description", "Employee Count", "Ownership", "Total Raised",
                "Date of Most Recent Investment", "Executive Title", "Executive First Name",
                "Executive Last Name", "Executive Email", "Investors", "2 Word Description"
            ]

            output_df = df[[col for col in final_columns if col in df.columns]].copy()
            output_df.rename(columns={
                "Employee Count": "Count",
                "Company Name": "Name"
            }, inplace=True)

            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = "attachment; filename=processed.csv"
            output_df.to_csv(response, index=False)
            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
