from django.core.cache import cache
from django.http import JsonResponse

from users.models import User


def check_progress(request):
    """
    Returns the current progress of file processing for the superuser from Django's cache.

    This function retrieves:
    - current: How many steps have been completed.
    - total: Total steps to complete.
    - percent: Percent complete.

    Args:
        request (HttpRequest): The incoming request (can be GET or AJAX).

    Returns:
        JsonResponse: A dictionary with progress values or a 0% fallback if no cache entry exists.
    """
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        return JsonResponse({"status": "error", "message": "User not found"}, status=404)

    progress = cache.get(f"progress_{user.id}")
    if not progress:
        return JsonResponse({"current": 0, "total": 0, "percent": 0})

    return JsonResponse(progress)
