from django.urls import path
from .views import *
from django.urls import include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from institution.views import StudentRegistrationAPIView


router = DefaultRouter()
# router.register("student/api",StudentViewSet,basename="StudentSignupAPI")
router.register("institution/api",InstitutionViewSet,basename="InstitutionSignupAPI")

urlpatterns = [
    path("signup/",include(router.urls)),
    path("signup/token/validator",StudentRegistrationAPIView.as_view(),name='decode_signup_token'),
   
   
   path("api/captcha/verify",CaptchaVerifyView.as_view(),name="captcha_verification"),
    
]
