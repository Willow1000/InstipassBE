from logs.models import APIAccessLog
from django.utils.deprecation import MiddlewareMixin
import threading
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from accounts.models import BannedIP
from django.conf import settings
from django.shortcuts import render

class APILogMiddleware:
    def __init__(self,get_response):
        self.get_response = get_response

    def __call__(self,request):
        if request.META:
            data =request.META
            x_forwarded_for = request.META.get("HTTP_X_FORWADED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get("REMOTE_ADDR")
        else:
            ip=None 
        response = self.get_response(request)
        user_id = str(request.user.id) if request.user.is_authenticated else "anonymous"
        if 'api' in request.path.lower():
            APIAccessLog.objects.create(
                user_id = user_id,
                endpoint = request.path,
                request_method = request.method,
                status_code = response.status_code,
                ip_address = ip
            )
 
        return response

# middleware.py


_request_local = threading.local()

def get_current_request():
    return getattr(_request_local, 'request', None)

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.request = request
        response = self.get_response(request)
        return response



def get_client_ip(request):
    # Respect X-Forwarded-For if behind proxy; otherwise fallback to REMOTE_ADDR
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

class IPBanMiddleware(MiddlewareMixin):
    """
    Blocks requests from currently banned IPs before they reach views.
    Returns 403 for normal browser requests, JSON 403 for API endpoints (heuristic).
    """

    def process_request(self, request):
        ip = get_client_ip(request)
        if not ip:
            return None

        # Optional fast path: if using Redis cache for quick checks, check that first.
        use_cache = getattr(settings, "IPBAN_USE_CACHE", False)
        if use_cache:
            # expected key/behavior: cache returns "banned" or timestamp
            from django.core.cache import cache
            key = f"bannedip:{ip}"
            cached = cache.get(key)
            if cached:
                # cached may be dict with banned_until etc
                return self._forbidden_response(request, ip, cached)

        # DB lookup
        try:
            ban = BannedIP.objects.get(ip_address=ip)
            if ban.is_active():
                return self._forbidden_response(request, ip, {"banned_until": ban.banned_until.isoformat(), "ban_count": ban.ban_count})
        except BannedIP.DoesNotExist:
            pass
        return None

    def _forbidden_response(self, request, ip, info):
        template_name = 'banned.html'
        # If API endpoint (simple heuristic: Accept header or path), return JSON error
        accepts = request.META.get("HTTP_ACCEPT", "")
        if "application/json" in accepts or request.path.startswith("/api/"):
            # print("here 1")
            return JsonResponse({"error": "ip_banned", "ip": ip, "info": info}, status=403)
        if "/super" in request.path:
            return render(template_name=template_name,request=request,)
        return  JsonResponse({"error": "ip_banned", "ip": ip, "info": info}, status=429)  

