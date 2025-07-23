from celery.result import AsyncResult
from django.core.cache import cache
from django.http import JsonResponse

from users.models import User


def task_status(request, task_id):
    """
    Returns the current status and progress of a background Celery task.

    - If the task is completed successfully, returns status 'completed' along with progress (100%)
      and the generated Excel file paths.
    - If the task failed, returns status 'error'.
    - If the task is still running, returns status 'pending' and the current progress percentage
      from the cache.

    Args:
        request (HttpRequest): The incoming HTTP request.
        task_id (str): The ID of the Celery task.

    Returns:
        JsonResponse: A JSON response with the task status and progress details.
    """
    result = AsyncResult(task_id)
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        return JsonResponse({"status": "error", "message": "User not found"}, status=404)
    percent = cache.get(f"{user.id}_progress", 0)

    if result.ready():
        if result.successful():
            data = result.result
            return JsonResponse({
                "status": "completed",
                "progress": 100,
                "processed_excel": data.get("processed_excel"),
                "action_excel": data.get("action_excel"),
            })
        else:
            return JsonResponse({"status": "error", "message": "Task failed"}, status=500)

    return JsonResponse({"status": "pending", "progress": percent})
