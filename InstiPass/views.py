# myapp/error_views.py
from django.shortcuts import render
from django.http import HttpResponse

# 404 Page Not Found
def error_404(request, exception):
    return render(request, "errors/404.html", status=404)

# 500 Server Error
def error_500(request):
    return render(request, "errors/500.html", status=500)

# 403 Permission Denied
def error_403(request, exception):
    return render(request, "errors/403.html", status=403)

# 401 Unauthorized
def error_401(request):
    return render(request, "errors/401.html", status=401)
