from django.http import HttpResponse

def flower_auth(request):
    # Se l'utente ha sessione valida e superuser -> 200, altrimenti 401
    if request.user.is_authenticated and request.user.is_superuser:
        return HttpResponse(status=200)
    return HttpResponse(status=401)