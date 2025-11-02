from django.urls import path,include
from rest_framework.routers import DefaultRouter,SimpleRouter
from .views import *
from InstiPass import settings
from django.conf.urls.static import static

from accounts.views import MagicLinkTokenVerifierAPIView,request_magic_link
from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from rest_framework.response import Response



router = DefaultRouter()
router.register("institution",InstitutionViewSet,basename="institutionApi")
router.register("institutions",InstitutionsViewSet,basename="institutionsApi")
router.register("settings",InstitutionSettingsViewSet,basename="institutionSettingsApi")
router.register("setings/studentform",InstitutionSettingsAllViewSet,basename="institutionSettingsAllApi")
router.register("notifications",NotificationViewSet,basename = "institutionNotificationsApi")
router.register('students',InstitutionStudentViewSet,basename='institutionStudents')
router.register("newsletter",NewsLetterViewSet,basename = 'newsletterAPI')
router.register("contactus",NotificationsViewSet,basename = "contactusAPI")
router.register('bookdemo',DemoBookingViewSet,basename="demobookingAPI")
router.register("report/issue",IssueViewSet,basename="reportIssueAPI")
router.register("testimonials",TestimonialViewSet,basename="testimonialsAPI")
# router.register("payment",PaymentViewSet,basename="paymentAPI")
router.register("verify/payment",PaymentProofVerificationViewSet,basename="paymentVerificationAPI")
router.register('balances',DeficitsViewSet,basename="InstitutionDeficitsAPI")

urlpatterns = [
    path('api/auth/verify/session/', MagicLinkTokenVerifierAPIView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path("api/",include(router.urls)),
    path("api/institution_stats/",IdProcessStatsAPIView.as_view(),name="id_process_stats"), 
    path("api/tokenvalidator",StudentRegistrationAPIView.as_view(),name='validate_token_institution'),
    path("api/signup/token/create",CreateInstitutionSignupTokenAPIView.as_view(),name="create_institution_signup_token"),
    path("api/login/token/create",CreateInstitutionLoginTokenAPIView.as_view(),name="create_institution_login_token"),
    path("api/registration/token/create",CreateInstitutionRegistrationTokenAPIView.as_view(),name="create_institution_registration_token"),
    path("api/student/registration/token/create",CreateStudentRegistrationTokenAPIView.as_view(),name="create_student_registration_token"),
    path("demobooking/conf/",ConfirmDemo.as_view(),name='confirm_demo'),
    path("api/verifier/student/",StudentVerificationView.as_view(),name="verify_student"),
    path("api/auth/request/link",request_magic_link),
    path('api/payment/',PaymentAPIView.as_view(),name="payment_api"),
    path('download/receipt/',download_receipt,name="download_receipt"),
    path("download/invoice/",download_invoice,name="download_invoice")
]


if settings.DEBUG:
    urlpatterns+= static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)