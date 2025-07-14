from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def upload_csv(request):
    if request.method == "POST":
        try:
            file = request.FILES["file"]
            path = default_storage.save(f"uploads/{file.name}", ContentFile(file.read()))
            file_url = default_storage.url(path)
            return JsonResponse({"status": "success", "file_url": file_url})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return render(request, "upload_csv.html")
