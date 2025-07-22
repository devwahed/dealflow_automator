import chardet
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from users.models import User
from users.tasks import process_file_task


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
        file = request.FILES["file"]
        raw_data = file.read()

        # Detect encoding
        result = chardet.detect(raw_data)
        encoding = result["encoding"] or "latin1"  # fallback if None

        try:
            file_data = raw_data.decode(encoding)
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"File decode failed: {str(e)}"}, status=400)

        filename = file.name.lower()

        user = User.objects.filter(is_superuser=True).first()
        if not user:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)

        task = process_file_task.delay(file_data, filename, user.id)
        return JsonResponse({"task_id": task.id}, status=200)
