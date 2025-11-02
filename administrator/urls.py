from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *
from institution.views import DeficitsAPIView


router = DefaultRouter()


urlpatterns = [
    path("login",AdminLogin.as_view(),name="adminLogin"),
    path("api/",include(router.urls)),
    path("messages",ContactUsView.as_view(),name="admin_contactus"),
    path("message/<int:pk>",DetailContactUsView.as_view(),name="admin_detail_contactus"),
    path("institutions",InstituttionsView.as_view(),name="institutions_admin"),
    path("",InstituttionsView.as_view(),name="institutions_admin"),
    path("institution/<int:pk>", InstitutionadminView.as_view(), name="institution_admin_detail"),
    path("logout",LogoutView.as_view(),name="adminLogout"),
    path("contactus/delete/<int:pk>",DelteContactUsView.as_view(),name="delete_contactus"),
    path("students/", StudentsAdminView.as_view(),name="students_admin"),
    path("delete/institution/<int:pk>",DeleteInstitutionView.as_view(),name="delete_institution"),
    path("delete/student/<int:pk>/",DeleteStudentView.as_view(),name="delete_student"),
    path('apiaccesslogs',ApiAccessView.as_view(),name="apiAccess"),
    path('update/student/<int:pk>/',StudentUpdateView.as_view(),name='update_student'),
    path("institution/registration/tracker/",RegistrationTrackerView.as_view(),name='institution_registration_tracker'),
    path('student/registration/tracker/',SubmissionTrackerView.as_view(),name = 'student_registration_tracker'),
    path('clear/apiaccess',clear_apiaccess_logs),
    path("clear/messages",clear_messages),
    path("clear/institution/tracker",clear_institution_reg_tracker),
    path("clear/student/tracker",clear_student_reg_tracker),
    path("institution/token",StudentRegistrationTokenView.as_view(),name='institution_token'),
    path('delete/token/<int:pk>/',DeleteTokenView.as_view(),name="delete_institution_token"),
    path('institution/signup/token',InstitutionSignupTokenView.as_view(),name='institution_signup_token'),
    path("institution/registration/token",InstitutionRegistrationTokenView.as_view(),name="institution_registration_token"),
    path("demobookings",DemoBookingView.as_view(),name="admin_demobooking"),
    path("demobookings/<int:pk>",DemoBookingDetailView.as_view(),name="admin_demosession_detail"),
    path("clear/institution/signup/token",clear_institution_signup_token),
    path("clear/institution/registration/token",clear_institution_registration_token),
    path("delete/demobooking/<int:pk>",DeleteDemoBooking.as_view(),name="delete_demobooking"),
    path("clear/demobookings",clear_demobooking),
    path("create/demosession", CreateDemoBooking.as_view(),name="admin_create_demosession"),
    path("reschedule/demosession/<int:pk>",UpdateDemoBooking.as_view(),name = "admin_reschedule_demosession"),
    path('institution/signup/tracker',SignupTrackerView.as_view(), name="admin_signup_tracker"),
    path('demobooking/tracker',DemoBookingTrackerView.as_view(),name='demobooking_tracker'),
    path('contactus/tracker',ContactUsTrackerView.as_view(),name='contactus_tracker'),
    path("clear/signuptracker",clear_signuptracker),
    path("clear/contactustracker",clear_contactustracker),
    path("clear/demobookingtracker",clear_demobookingtracker),
    path('blacklist/<str:institution_email>', blacklist_manager, name='blacklist_user'),
    path("usermanagement",UserView.as_view(),name="user_management" ),
    path("delete/user/<int:pk>",DeleteUserView.as_view(),name='delete_user'),
    path("issues",IssueView.as_view(),name="admin_issue_view"),
    path("clear/resolved/issues",clear_resolved_issues),
    path("accept/issue/",accept_issue,name="admin_accept_issue"),
    path("issue/resolved/",resolved_issue,name="issue_resolved"),
    path("issues/<int:pk>",IssueDetailView.as_view(),name="issue_detail"),
    path("demo/complete/<int:pk>",demo_complete,name="admin_demo_completed"),
    path("demo/cancelled/<int:pk>",demo_cancelled,name="admin_demo_cancelled"),
    path("payments",PaymentView.as_view(),name="admin_payments_view"),
    path("verify/payment/<int:pk>/",verify_payment,name="admin_approve_payment"),
    path("reject/payment/<int:pk>/",reject_payment,name="admin_reject_payment"),

    path("clear/expired/student/tokens",clear_expired_student_registration_tokens),
    path("institution/login/token",InstitutionLoginToken.as_view(),name="institution_login_token_view"),
    path("clear/institution/login/token",clear_institution_login_token,name="clear_institution_login_token"),

    path('export-tool/', ExportToolView.as_view(), name='admin_export_tool'),
    path('api/export/schema/', SchemaAPIView.as_view(), name='schema_api'),
    path('api/export/data/', ExportAPIView.as_view(), name='export_api'),
    path('api/export/logs/', ExportLogsAPIView.as_view(), name='export_logs_api'),
    path('api/export/preview/', PreviewAPIView.as_view(), name='export_preview_api'),

    path("api/verification/payment",PaymentProofVerificationView.as_view(),name="admin_payment_proof"),
    path("receipt/download/tokens",ReceiptDownloadTokenView.as_view(),name="receipt_download_token_view"),
    path("clear/receipt/download/tokens/",clear_receipt_download_token,name="clear_receipt_download_tokens"),
    path("deficits",DeficitsView.as_view(),name="admin_deficits_view"),
    path("send/invoice/<int:pk>",send_invoice,name="send_invoice"),
    path("invoice/download/tokens",InvoiceDownloadTokenView.as_view(),name="invoice_download_tokens"),
    path("clear/invoice/download/tokens/",clear_invoice_download_token,name="clear_invoice_download_tokens"),
    path("create/deficit/",DeficitsAPIView.as_view(),name="create_deficit"),

    path('login/tracker',LoginTrackerView.as_view(),name="admin_login_tracker"),
    path("clear/login/tracker",clear_institution_login_tracker,name="clear_login_tracker")
]

