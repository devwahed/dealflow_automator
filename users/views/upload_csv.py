import io
import base64

import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from users.models import User
from users.models import UserConfiguration
from users.utilities import generate_descriptions_and_tiers_with_progress, clear_progress


@method_decorator(csrf_exempt, name='dispatch')
class UploadAndTierView(View):
    """
    Handles the uploading of a CSV or Excel file, processes it using tiering logic,
    generates descriptions and product tiers using GPT, and returns two CSV outputs.

    - GET: Renders the upload form.
    - POST: Processes the uploaded file and applies tier logic + LLM-based enhancements.
    """

    def get(self, request):
        """
        Renders the upload page with a file input form.

        Returns:
            HttpResponse: Renders the 'upload_csv.html' template.
        """
        return render(request, "upload_csv.html")

    def post(self, request):
        """
        Processes an uploaded CSV or Excel file by:
        - Reading the file and converting to a DataFrame.
        - Applying tiering logic (country, ownership, funding, etc.) based on config.
        - Generating product tiers and short descriptions via GPT.
        - Returning two processed CSVs: one clean, one for UI display.

        Args:
            request (HttpRequest): The incoming POST request containing the uploaded file.

        Returns:
            JsonResponse: Contains two CSV outputs as strings:
                - 'processed_csv': Cleaned and finalized data.
                - 'action_csv': Intermediate data used for UI sorting/filtering.

        Raises:
            JsonResponse: With an error message if something fails during processing.
        """
        try:
            file = request.FILES["file"]
            filename = file.name.lower()

            user = User.objects.filter(is_superuser=True).first()
            if not user:
                return JsonResponse({"status": "error", "message": "User not found"}, status=404)

            config = UserConfiguration.objects.get(user=user).configuration_json

            # Read file
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

            df["Pre-Product Tier"] = df[
                ["country_tier", "ownership_tier", "founding_tier", "fundraise_tier", "raised_tier", "fte_tier"]].max(
                axis=1)

            # GPT-based logic
            product_tiers, descriptions = generate_descriptions_and_tiers_with_progress(df, user.id)
            df["Product Tier - CHAT GPT"] = pd.Series(pd.to_numeric(product_tiers, errors="coerce")).fillna(0)
            df["2 Word Description"] = descriptions

            df["Post Tier"] = df[["Pre-Product Tier", "Product Tier - CHAT GPT"]].max(axis=1)
            df["Index"] = df.index + 1
            df["Post_Order"] = df["Post Tier"] * 10000 - df["Index"]
            df["Post Rank"] = df["Post_Order"].rank(method="min", ascending=True).astype(int)
            df["Tier"] = df["Post Tier"]

            # Remove Tier 4 companies
            df = df[df["Post Tier"] != 4]

            # Sort by Tier ASC and Employee Count DESC
            df = df.sort_values(by=["Post Tier", "Employee Count"], ascending=[True, False])

            # === PROCESSED FILE ===
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

            # === ACTION FILE ===
            df["2 Word Description - CHAT GPT"] = df["2 Word Description"]
            df["Include"] = ""

            action_columns = [
                "Pre-Product Tier", "Post Tier", "Post_Order", "Post Rank", "Index",
                "Include", "Company Name", "Website", "Description", "Employee Count",
                "Product Tier - CHAT GPT", "2 Word Description - CHAT GPT"
            ]

            action_df = df[[col for col in action_columns if col in df.columns]].copy()

            # Write Excel files in-memory
            processed_output = io.BytesIO()
            action_output = io.BytesIO()

            # === Processed File ===
            with pd.ExcelWriter(processed_output, engine="xlsxwriter") as writer:
                processed_df.to_excel(writer, index=False, sheet_name="Processed")

                workbook = writer.book
                worksheet = writer.sheets["Processed"]

                # Define header and wrap formats
                header_format = workbook.add_format({
                    "bold": True,
                    "bg_color": "#3B87AD",
                    "font_color": "white",
                    "text_wrap": True,
                    "align": "center",
                    "valign": "center"
                })

                wrap_format = workbook.add_format({
                    "text_wrap": True,
                    "valign": "top"
                })

                # Apply header format
                for col_num, value in enumerate(processed_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Apply wrap format to entire data range
                worksheet.set_column(0, len(processed_df.columns) - 1, 20, wrap_format)

            # === Action File ===
            with pd.ExcelWriter(action_output, engine="xlsxwriter") as writer:
                action_df.to_excel(writer, index=False, sheet_name="Action")

                workbook_a = writer.book
                worksheet_a = writer.sheets["Action"]

                header_format_a = workbook_a.add_format({
                    "bold": True,
                    "bg_color": "#3B87AD",
                    "font_color": "white",
                    "text_wrap": True,
                    "align": "center",
                    "valign": "center"
                })

                wrap_format_a = workbook_a.add_format({
                    "text_wrap": True,
                    "valign": "top"
                })

                for col_num, value in enumerate(action_df.columns.values):
                    worksheet_a.write(0, col_num, value, header_format_a)

                worksheet_a.set_column(0, len(action_df.columns) - 1, 20, wrap_format_a)

            processed_output.seek(0)
            action_output.seek(0)

            clear_progress(user.id)

            return JsonResponse({
                "processed_excel": base64.b64encode(processed_output.getvalue()).decode(),
                "action_excel": base64.b64encode(action_output.getvalue()).decode(),
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)