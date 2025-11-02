from django.contrib import admin
from InstiPass import settings
from django.conf.urls.static import static
from django.urls import path,include
from .views import *
from accounts.models import User

from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
# from . import view

# from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

class OTPAdmin(OTPAdminSite):
    pass

admin_site = OTPAdmin(name='OTPAdmin')
admin_site.register(User)
admin_site.register(TOTPDevice,TOTPDeviceAdmin)

if User not in admin_site._registry:
    admin_site.register(User)


if TOTPDevice not in admin_site._registry:
    admin_site.register(TOTPDevice,TOTPDeviceAdmin)


for model_cls,model_admin in admin.site._registry.items():
    if model_cls not in admin_site._registry:
        admin_site.register(model_cls,model_admin.__class__)



urlpatterns = [
    path('admin/', admin_site.urls),
    path("",include('accounts.urls')),
   
    path("superuser/",include("Id.urls")),
    path("institution/",include('institution.urls')),
    path("student/",include('student.urls')),
    path("super/",include("administrator.urls")),

   
    # DRF Spectacular URLs (no UI):
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
# urls.py



if settings.DEBUG:
    urlpatterns+= static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

handler404 = error_404
handler500 = error_500
handler403 = error_403