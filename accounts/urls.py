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
    # path('password-reset/', 
    #  PasswordResetView.as_view(

    #      template_name='password_reset_form.html',
    #      email_template_name='password_reset_email.html',
    #      subject_template_name='registration/password_reset_subject.txt',
    #     #  success_url=
    #  ), 
    #  name='password_reset'),
    #  path(
    #     'password-reset/confirm/<uidb64>/<token>/',
    #     auth_views.PasswordResetConfirmView.as_view(
    #         template_name='password_reset_conf.html',  # your custom template
    #         success_url='../../../../reset/done/'  # optional
    #     ),
    #     name='password_reset_confirm'
    # ),
    # path('password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),

    # path('reset/done/', PasswordResetSuccessView.as_view(), name='password_reset_complete'),
   
   path("api/captcha/verify",CaptchaVerifyView.as_view(),name="captcha_verification"),
    
]
