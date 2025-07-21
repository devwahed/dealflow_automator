import json
import os

from django.http import JsonResponse

from users.models import User
from users.utilities import get_progress_file_path


def check_progress(request):
    """
    Returns the current progress of file processing for the superuser.

    This function checks the JSON progress file and reports:
    - current: How many steps have been completed.
    - total: Total steps to complete.
    - percent: Percent complete.

    Args:
        request (HttpRequest): The incoming request (can be GET or AJAX).

    Returns:
        JsonResponse: A dictionary with progress values or a 0% fallback if no file exists.
    """
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        return JsonResponse({"status": "error", "message": "User not found"}, status=404)
    path = get_progress_file_path(user.id)
    if not os.path.exists(path):
        return JsonResponse({"current": 0, "total": 0, "percent": 0})
    with open(path, "r") as f:
        return JsonResponse(json.load(f))
