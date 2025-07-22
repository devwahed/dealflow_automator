from celery.result import AsyncResult
from django.http import JsonResponse
from django.views import View


class TaskStatusView(View):
    def get(self, request, task_id):
        result = AsyncResult(task_id)

        if result.state == 'PENDING':
            return JsonResponse({"status": "PENDING"}, status=202)
        elif result.state == 'FAILURE':
            return JsonResponse({"status": "FAILURE", "error": str(result.result)}, status=500)
        elif result.state == 'SUCCESS':
            return JsonResponse({
                "status": "SUCCESS",
                "processed_csv": result.result.get("processed_csv", ""),
                "action_csv": result.result.get("action_csv", "")
            }, status=200)
        else:
            return JsonResponse({"status": result.state}, status=202)
