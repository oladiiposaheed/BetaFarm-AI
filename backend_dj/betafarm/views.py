from django.http import JsonResponse

def home_view(request):
    return JsonResponse({
        "service": "BetaFarm AI API",
        "status": "running",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/",
        }
    })