import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from users.models import UserConfiguration
from users.models.user import User


def configuration(request):
    return render(request, template_name='index.html')


@csrf_exempt
def submit_configuration(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            superuser = User.objects.filter(is_superuser=True).first()
            if not superuser:
                return JsonResponse({"status": "error", "message": "Superuser not found"}, status=404)

            user_config, _ = UserConfiguration.objects.get_or_create(user=superuser)
            user_config.configuration_json = data
            user_config.save()

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"error": "Invalid method"}, status=405)


def get_configuration(request):
    superuser = User.objects.filter(is_superuser=True).first()
    if not superuser:
        return JsonResponse({"status": "error", "message": "Superuser not found"}, status=404)

    try:
        config = UserConfiguration.objects.get(user=superuser)
        config_data = config.configuration_json
        if hasattr(config_data, 'items'):
            config_data = dict(config_data)

        return JsonResponse({"status": "success", "data": config_data})

    except UserConfiguration.DoesNotExist:
        return JsonResponse({"status": "empty", "data": {}})
