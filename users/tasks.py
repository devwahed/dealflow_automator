from celery import shared_task

from .utilities import generate_descriptions_and_tiers_with_progress, clear_progress, save_progress


@shared_task(bind=True)
def process_uploaded_file(self, file_data_b64, filename, user_id):
    """
    Celery task to process an uploaded file (CSV or Excel) containing company data.

    Steps:
    - Decodes the base64-encoded file.
    - Loads it into a pandas DataFrame and cleans/prepares numeric fields.
    - Applies tiering logic based on user-specific configuration:
        - Founding year, fundraiser date, total raised, FTE, ownership, and country.
    - Tracks and saves progress in cache per user.
    - Uses GPT-based helpers to generate product tiers and business descriptions.
    - Computes final rankings and filters Tier 4 companies.
    - Outputs two Excel files:
        - Processed: For presentation.
        - Action: For internal use, includes GPT-generated data.
    - Returns both files as base64-encoded strings.

    Args:
        self: Celery task instance (for binding).
        file_data_b64 (str): Base64-encoded file content.
        filename (str): Name of the uploaded file (to determine file type).
        user_id (int): ID of the user initiating the task (used for config & progress).

    Returns:
        dict: A dictionary with:
            - "status": "success" or "error"
            - "processed_excel": base64-encoded processed Excel file (if success)
            - "action_excel": base64-encoded action Excel file (if success)
            - "message": error message (if error)
    """
    try:
        from users.models import User
        import base64, io, pandas as pd

        file_data = base64.b64decode(file_data_b64)
        user = User.objects.filter(id=user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}

        config = user.configuration.configuration_json

        # Clear any previous progress
        clear_progress(user_id)

        # Load DataFrame
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(file_data), encoding="utf-8")
            except Exception:
                df = pd.read_csv(io.BytesIO(file_data), encoding="latin1")
        else:
            df = pd.read_excel(io.BytesIO(file_data))

        df = df[df["Company Name"].notna()].reset_index(drop=True)
        df["Founding Year"] = pd.to_numeric(df.get("Founding Year"), errors="coerce")
        df["Total Raised"] = pd.to_numeric(df.get("Total Raised"), errors="coerce")
        df["Employee Count"] = pd.to_numeric(df.get("Employee Count"), errors="coerce")

        # Tiers
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
            except Exception:
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
                    except Exception:
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
            except Exception:
                return None
            return 4

        # Apply tiering
        df["country_tier"] = df["Country"].map(config.get("country", {}))
        df["ownership_tier"] = df["Ownership"].map(config.get("Ownership", {}))
        df["founding_tier"] = df["Founding Year"].apply(get_founding_tier)
        df["fundraise_tier"] = df["Date of Most Recent Investment"].apply(get_fundraise_tier)
        df["raised_tier"] = df.apply(get_total_raised_tier, axis=1)
        df["fte_tier"] = df.apply(get_fte_tier, axis=1)

        df["Pre-Product Tier"] = df[[  # max of all rules
            "country_tier", "ownership_tier", "founding_tier",
            "fundraise_tier", "raised_tier", "fte_tier"
        ]].max(axis=1)

        # GPT logic with progress tracking
        product_tiers, descriptions = generate_descriptions_and_tiers_with_progress(df, user.id)

        df["Product Tier - CHAT GPT"] = pd.Series(pd.to_numeric(product_tiers, errors="coerce")).fillna(0)
        df["2 Word Description"] = descriptions

        df["Post Tier"] = df[["Pre-Product Tier", "Product Tier - CHAT GPT"]].max(axis=1)
        df["Index"] = df.index + 1
        df["Post_Order"] = df["Post Tier"] * 10000 - df["Index"]
        df["Post Rank"] = df["Post_Order"].rank(method="min", ascending=True).astype(int)
        df["Tier"] = df["Post Tier"]

        # Filter Tier 4
        df = df[df["Post Tier"] != 4]
        df = df.sort_values(by=["Post Tier", "Employee Count"], ascending=[True, False])

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

        # Action sheet
        df["2 Word Description - CHAT GPT"] = df["2 Word Description"]
        df["Include"] = ""
        action_columns = [
            "Pre-Product Tier", "Post Tier", "Post_Order", "Post Rank", "Index",
            "Include", "Company Name", "Website", "Description", "Employee Count",
            "Product Tier - CHAT GPT", "2 Word Description - CHAT GPT"
        ]
        action_df = df[[col for col in action_columns if col in df.columns]].copy()

        # Create Excel files
        processed_output = io.BytesIO()
        action_output = io.BytesIO()

        def write_excel(output, data, sheet_name):
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                data.to_excel(writer, index=False, sheet_name=sheet_name)
                workbook = writer.book
                worksheet = writer.sheets[sheet_name]

                header_format = workbook.add_format({
                    "bold": True, "bg_color": "#3B87AD", "font_color": "white",
                    "text_wrap": True, "align": "center", "valign": "center"
                })
                wrap_format = workbook.add_format({
                    "text_wrap": True, "valign": "top"
                })

                for col_num, value in enumerate(data.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                worksheet.set_column(0, len(data.columns) - 1, 20, wrap_format)

        write_excel(processed_output, processed_df, "Processed")
        write_excel(action_output, action_df, "Action")

        processed_output.seek(0)
        action_output.seek(0)

        # Mark progress 100% only at the very end
        save_progress(user.id, 100, 100)

        return {
            "status": "success",
            "processed_excel": base64.b64encode(processed_output.getvalue()).decode(),
            "action_excel": base64.b64encode(action_output.getvalue()).decode(),
        }

    except Exception as e:
        save_progress(user_id, 1, 1)
        return {"status": "error", "message": str(e)}
