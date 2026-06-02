def home(request):
    import traceback
    try:
        return HttpResponse("BetaFarm AI API is running!")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}\n{traceback.format_exc()}", status=500)