import base64

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from users.models import User
from users.tasks import process_uploaded_file
from users.utilities import save_progress


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
        Handles file upload and initiates background processing using Celery.

        - Validates the presence of a superuser and uploaded file.
        - Reads the uploaded file, encodes it to base64, and sends it to a Celery task.
        - Stores initial progress in the cache and returns the task ID for tracking.

        Args:
            request (HttpRequest): The incoming POST request containing the file.

        Returns:
            JsonResponse: A JSON response with either an error message or the Celery task ID.
        """
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)

        file = request.FILES.get("file")
        if not file:
            return JsonResponse({"status": "error", "message": "No file uploaded"}, status=400)

        filename = file.name.lower()
        file_data_b64 = base64.b64encode(file.read()).decode()

        # Start Celery task
        save_progress(user.id, 0, 1)
        task = process_uploaded_file.delay(file_data_b64, filename, user.id)

        return JsonResponse({"status": "success", "task_id": task.id}, status=200)
