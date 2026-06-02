from django.http import JsonResponse
from django.shortcuts import render


def home_view(request):
    return JsonResponse({
        "service": "BetaFarm AI API",
        "status": "running",
        "endpoints": {
            "admin": "/admin/",
            "api": "/api/",
        }
    })
    
    
def index_view(request):
    '''Serve the main frontend page.'''
    return render(request, 'index.html')