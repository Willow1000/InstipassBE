from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import ListView,UpdateView,DeleteView,DetailView,CreateView
from django.contrib.auth.views import LoginView,LogoutView
from django.contrib.auth import logout
from .forms import LoginForm
from django.shortcuts import redirect
from institution.models import *
import requests
from datetime import datetime
from rest_framework import viewsets,status
from student.models import *
from django.shortcuts import get_object_or_404
import json
from .models import ContactUsTracker,DemoBookingTracker
from django.contrib import messages
from logs.models import APIAccessLog,AdminActionsLog,BlackListLog,TransactionsLog
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from accounts.models import InstitutionSignupToken, SignupTracker,InstitutionRegistrationToken,User
# from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import action
from django.views.decorators.csrf import ensure_csrf_cookie
from institution.views import get_client_ip
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from logs.models import DemoLogs
from django.utils.html import strip_tags


from django.http import  HttpResponse
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db import models

from InstiPass.services import SchemaService
from InstiPass.export_service import ExportService
from logs.models import ExportLog
from institution.utils import generate_login_token


from django.contrib.auth import authenticate,login
from django.shortcuts import render,reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from django.db.models import Q
from django.utils import timezone

class AdminLogin(LoginView):
    template_name = "administrator/admin_login.html"
    redirect_authenticated_user = True
    form_class = LoginForm

    def post(self, request, *args, **kwargs):
        username = request.POST.get("username")
        password = request.POST.get("password")
        otp = request.POST.get("otp")

        # Step 1: Validate credentials
        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            device = TOTPDevice.objects.filter(user=user).first()

            # Step 2: OTP verification
            if device and device.verify_token(otp):
                login(request, user)

                # 🧠 THIS handles ?next=
                return redirect(self.get_success_url())

            return render(request, self.template_name, {
                "error": "Invalid OTP",
                "username": username,
            })

        return render(request, self.template_name, {
            "error": "Invalid credentials",
            "username": username,
        })

    def get_success_url(self):
        # Django automatically extracts ?next=
        return self.get_redirect_url() or reverse("institutions_admin")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect("institutions_admin")
        return super().dispatch(request, *args, **kwargs)
    
class LogoutView(LogoutView):
    next_page = "/super/login?next=institutions"   
    def dispatch(self, request, *args, **kwargs):
        logout(request)  # Ensure session is cleared
        return redirect(self.next_page)

class InstituttionsView(LoginRequiredMixin,UserPassesTestMixin,ListView):
        model = Institution
        template_name = "administrator/admin_institution.html"
        context_object_name = "institutions"
        login_url = reverse_lazy('adminLogin')

        def get_queryset(self):
            query = self.request.GET.get('querry')
            if query:
                return Institution.objects.filter(name__icontains=query).order_by('created_at') | Institution.objects.filter(region__icontains=query).order_by('created_at') | Institution.objects.filter(county__icontains=query).order_by('-created_at')
            return Institution.objects.all().order_by('created_at')
        def test_func(self):
            return self.request.user.is_superuser
        
class InstitutionadminView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = Institution
    template_name = "administrator/admin_institution_detail.html"
    context_object_name = "institution"
    login_url = reverse_lazy('adminLogin')
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs.get("pk")
        institution = get_object_or_404(Institution, id=pk)
        context['settings'] = InstitutionSettings.objects.filter(institution=institution).first()

        if self.request.user.is_authenticated:
            try:
                with requests.Session() as session:
                    session.cookies.set("sessionid", self.request.COOKIES.get("sessionid"))
                    session.cookies.set("csrftoken", self.request.COOKIES.get("csrftoken"))
                    headers = {
                        "X-CSRFToken": self.request.COOKIES.get("csrftoken")
                    }
                    response = session.get(
                        f"http://127.0.0.1:8000/institution/api/institution_stats/?q={institution.email}",
                        headers=headers
                    )
                    data = response.json()
                    context['total'] = data.get("registered_students")
                    context['expected'] = data.get("expected")
                    context["ready"] = data.get("Ids_ready")
            except Exception as e:
                print(f"Error fetching stats: {e}")
                context['total'] = context['process'] = context['ready'] = 0
            return context

    def test_func(self):
            return self.request.user.is_superuser

class StudentRegistrationTokenView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = StudentRegistrationToken
    template_name = 'administrator/admin_institution_token.html'
    login_url = reverse_lazy("adminLogin")
    context_object_name = 'tokens'
    def test_func(self):
        return self.request.user.is_superuser

    def get_context_data(self,**kwargs):
        context = context = super().get_context_data(**kwargs)

        context['institutions'] = Institution.objects.all()

        return context

class DeleteTokenView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = StudentRegistrationToken
    success_url = reverse_lazy('institution_token')
    login_url = reverse_lazy('adminLogin')       

    def test_func(self):
        return self.request.user.is_superuser

class DeleteInstitutionView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = Institution
    success_url = reverse_lazy("institutions_admin")
    login_url = reverse_lazy('adminLogin')
    
    def test_func(self):
        return self.request.user.is_superuser

class DeleteStudentView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = Student
    login_url = reverse_lazy('adminLogin')
    def test_func(self):
        return self.request.user.is_superuser
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url 

class StudentsAdminView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Student
    template_name = "administrator/admin_student.html"
    login_url = reverse_lazy('adminLogin')
    context_object_name = "students"

    def get_queryset(self):
        email = self.request.GET.get("q")
        institution = Institution.objects.filter(email=email).first()
        return Student.objects.filter(
            institution=institution
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        email = self.request.GET.get("q")
        institution = Institution.objects.filter(email=email).first()
        context["institution"] = institution
        return context

    def test_func(self):
        return self.request.user.is_superuser


class StudentUpdateView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model=Student
    template_name = "administrator/admin_student_update.html"
    login_url = reverse_lazy("adminLogin")
    fields = ['first_name','last_name','email','phone_number','reg_no','course','admission_year','photo']
    
    def test_func(self):
        return self.request.user.is_superuser 

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url     


class ApiAccessView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    template_name = 'administrator/admin_apiaccesslogs.html'
    model = APIAccessLog  
    login_url = reverse_lazy('adminLogin')
    context_object_name = 'logs'

    def test_func(self):
        return self.request.user.is_superuser      



@login_required
@user_passes_test(lambda u: u.is_superuser)
def blacklist_manager(request, institution_email):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            reason_category = data.get("reason_category")
            reason_explanation = data.get("reason_explanation")
            action_type = data.get("action") # 'blacklist' or 'unblacklist'
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON in request body"}, status=400)

        if not reason_category or not reason_explanation or not action_type:
            return JsonResponse({"error": "Reason category, explanation, and action are required."}, status=400)

        user_to_manage = get_object_or_404(User, email=institution_email)

        if user_to_manage == request.user:
            return JsonResponse({"error": "You can't blacklist/unblacklist yourself."}, status=403)

        # Determine action based on current state and requested action_type
        if action_type == "blacklist":
            if not user_to_manage.is_active:
                return JsonResponse({"message": f"{user_to_manage.email} is already blacklisted."}, status=200)
            user_to_manage.is_active = False
            action_log = "blacklisted"
            success_message = f"{user_to_manage.email} has been blacklisted."
        elif action_type == "unblacklist":
            if user_to_manage.is_active:
                return JsonResponse({"message": f"{user_to_manage.email} is not blacklisted."}, status=200)
            user_to_manage.is_active = True
            action_log = "unblacklisted"
            success_message = f"{user_to_manage.email} has been removed from the blacklist."
        else:
            return JsonResponse({"error": "Invalid action type provided."}, status=400)

        user_to_manage.save()

        # Log the action
        BlackListLog.objects.create(
            action=action_log,
            admin=request.user,
            victim=user_to_manage,
            reason_category=reason_category,
            reason_explanation=reason_explanation
        )

        # Use JsonResponse for AJAX requests
        return JsonResponse({"message": success_message, "is_active": user_to_manage.is_active}, status=200)

    return HttpResponseForbidden("Only POST requests are allowed.")




@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_apiaccess_logs(request):
    try:
        deleted_count, _ = APIAccessLog.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} logs.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "APIACCESSLOGS",
            victim = f"{deleted_count} APIACCESSLOGS"

        )
        return redirect(referer)
        
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_messages(request):
    try:
        deleted_count, _ = ContactUs.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} messages.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "MESSAGES",
            victim = f"{deleted_count} MESSAGES"

        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)  

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_student_reg_tracker(request):
    try:
        deleted_count, _ = SubmissionTracker.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} logs.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "STUDENTREGISTRATIONTRACKERLOGS",
            victim = f"{deleted_count} STUDENTREGISTRATIONTRACKERLOGS"

        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_institution_reg_tracker(request):
    try:
        deleted_count, _ = RegistrationTracker.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} logs.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "INSTITUTIONREGISTRATIONTRACKERLOGS",
            victim = f"{deleted_count} INSTITUTIONREGISTRATIONTRACKERLOGS"

        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)  

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_institution_login_tracker(request):
    try:
        deleted_count, _ = LoginTracker.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} logs.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "INSTITUTIONLOGINTRACKERLOGS",
            victim = f"{deleted_count} INSTITUTIONLOGINTRACKERLOGS"

        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)  

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_institution_signup_token(request):
    try:
        used_tokens = InstitutionSignupToken.objects.filter(Q(used=True) | Q(expiry_date__lt=timezone.now()))
        referer = request.META.get('HTTP_REFERER') or '/'
        if used_tokens:
            deleted_count, _ = used_tokens.delete()
            messages.success(request, f"Deleted {deleted_count} tokens.")
            
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "INSTITUTIONSIGNUPTOKENS",
                victim = f"{deleted_count} INSTITUTIONSIGNUPTOKENS"

            )
        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)
          
        # messages.success(request, f"Deleted {deleted_count} tokens.")
        # referer = request.META.get('HTTP_REFERER') or '/'

        # return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500) 


# from yourapp.models import InstitutionMagicLinkToken

tokens = InstitutionMagicLinkToken.objects.filter(
    Q(used=True) | Q(expiry_date__lt=timezone.now())
)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_institution_login_token(request):
    try:
        used_tokens = InstitutionMagicLinkToken.objects.filter(Q(used=True) | Q(expiry_date__lt=timezone.now()))
        referer = request.META.get('HTTP_REFERER') or '/'
        if used_tokens:
            deleted_count, _ = used_tokens.delete()
            messages.success(request, f"Deleted {deleted_count} tokens.")
            
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "INSTITUTIONLOGINTOKENS",
                victim = f"{deleted_count} INSTITUTIONLOGINTOKENS"

            )
        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)
          
        # messages.success(request, f"Deleted {deleted_count} tokens.")
        # referer = request.META.get('HTTP_REFERER') or '/'

        # return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500) 
@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_receipt_download_token(request):
    try:
        used_tokens= PaymentReceiptDownloadToken.objects.filter(Q(used=True) | Q(expiry_date__lt=timezone.now()))
        referer = request.META.get('HTTP_REFERER') or '/'
        if used_tokens:
            deleted_count, _ = used_tokens.delete()
            messages.success(request, f"Deleted {deleted_count} tokens.")
            
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "RECEIPTDOWNLOADTOKENS",
                victim = f"{deleted_count} RECEIPTDOWNLOADTOKENS"

            )
        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)
          
        # messages.success(request, f"Deleted {deleted_count} tokens.")
        # referer = request.META.get('HTTP_REFERER') or '/'

        # return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_invoice_download_token(request):
    try:
        used_tokens = InvoiceDownloadToken.objects.filter(Q(used=True) | Q(expiry_date__lt=timezone.now()))
        referer = request.META.get('HTTP_REFERER') or '/'
        if used_tokens:
            deleted_count, _ = used_tokens.delete()
            messages.success(request, f"Deleted {deleted_count} tokens.")
            
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "INVOICEDOWNLOADTOKENS",
                victim = f"{deleted_count} INVOICEDOWNLOADTOKENS"

            )
        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)
          
        # messages.success(request, f"Deleted {deleted_count} tokens.")
        # referer = request.META.get('HTTP_REFERER') or '/'

        # return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_institution_registration_token(request):
    try:
        used_tokens = InstitutionRegistrationToken.objects.filter(Q(used=True) | Q(expiry_date__lt=timezone.now()))
        referer = request.META.get('HTTP_REFERER') or '/'
        if used_tokens:
            deleted_count, _ = used_tokens.delete()
            messages.success(request, f"Deleted {deleted_count} tokens.")
            
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "INSTITUTIONREGISTRATIONTOKENS",
                victim = f"{deleted_count} INSTITUTIONREGISTRATIONTOKENS"

            )
        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500) 


@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_demobooking(request):
    try:
        cancelled = DemoBooking.objects.filter(status="CANCELLED")
        completed = DemoBooking.objects.filter(status="COMPLETED")
        referer = request.META.get('HTTP_REFERER') or '/'
        if cancelled or completed:
            deleted_count=0
            if cancelled:
                deleted_count_cancelled, _ =cancelled.delete()
                deleted_count+=deleted_count_cancelled
            if completed:
                deleted_count_completed, _ =completed.delete()
                deleted_count+=deleted_count_completed
            messages.success(request, f"Deleted {deleted_count} demobookings.")
            referer = request.META.get('HTTP_REFERER') or '/'
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "DEMOBOOKINGS",
                victim = f"{deleted_count} DEMOBOOKINGS"

            )

        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)   

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_signuptracker(request):
    try:
        deleted_count, _ = SignupTracker.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} signuptracker records.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "SIGNUPTRACKER",
            victim = f"{deleted_count} SIGNUPTRACKERLOGS"

        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)          

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_demobookingtracker(request):
    try:
        deleted_count, _ = DemoBookingTracker.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} demobookingtracker records.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "DEMOBOKINGTRACKER",
            victim = f"{deleted_count} DEMOBBOKINGTRACKERLOGS"

        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)  

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_contactustracker(request):
    try:
        deleted_count, _ = ContactUsTracker.objects.all().delete()
        messages.success(request, f"Deleted {deleted_count} contactustracker records.")
        referer = request.META.get('HTTP_REFERER') or '/'
        AdminActionsLog.objects.create(
            action = "CLEAR",
            admin = request.user,
            victim_type = "CONTACTUSTRACKER",
            victim = f"{deleted_count} CONTACTUSTRACKERLOGS"

        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)      


@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_resolved_issues(request):
    try:
        referer = request.META.get('HTTP_REFERER') or '/'
        if Issue.objects.filter(status = 'resolved'):
            deleted_count, _ = Issue.objects.filter(status = 'resolved').delete()
            messages.success(request, f"Deleted {deleted_count} resolved issues.")
            
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "RESOLVED ISSUES",
                victim = f"{deleted_count} RESOLVEDISSUES"

            )
        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)
          
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)      

@login_required
@user_passes_test(lambda u: u.is_superuser)
def accept_issue(request):
    try:
        referer = request.META.get('HTTP_REFERER') or '/'
        id = int(request.GET.get('issue_id'))
        admin = request.user
        issue = get_object_or_404(Issue,id=id)
        issue.assigned_to = admin
        issue.status = "in_progress"
        issue.save()
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500) 

@login_required
@user_passes_test(lambda u: u.is_superuser)
def resolved_issue(request):
    try:
        referer = request.META.get('HTTP_REFERER') or '/'
        id = int(request.GET.get('issue_id'))
        admin = request.user
        issue = get_object_or_404(Issue,id=id)
        issue.status = "resolved"
        issue.resolved_at = timezone.now()
        issue.save()
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)  

@login_required
@user_passes_test(lambda u: u.is_superuser)
def demo_complete(request,pk):
    referer = request.META.get('HTTP_REFERER') or '/'
    try:
        demo = get_object_or_404(DemoBooking, id=pk)
        demo.status = "COMPLETED"
        demo.save()
        template_name = 'emailtemplates/demo_complete.html'
        html_message = render_to_string(template_name)
        
        # Create plain text version for email clients that don't support HTML
        plain_message = strip_tags(html_message)
        
        # Send email with both HTML and plain text versions
        send_mail(
            subject='Demo Session Complete',
            message=plain_message,
            from_email='demos@instipass.com',
            recipient_list=['wilkinsondari7@gmail.com'],
            fail_silently=False,
            html_message=html_message,)
        
        DemoLogs.objects.create(
            admin = request.user,
            demo = demo,
            action = "Marked as Complete"
        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)     

@login_required
@user_passes_test(lambda u: u.is_superuser)
def demo_cancelled(request,pk):
    referer = request.META.get('HTTP_REFERER') or '/'
    try:
        demo = get_object_or_404(DemoBooking, id=pk)
        demo.status = "CANCELLED"
        demo.save()

        DemoLogs.objects.create(
            admin = request.user,
            demo = demo,
            action = "Marked as Cancelled"
        )
        return redirect(referer)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)    

@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_expired_student_registration_tokens(request):
    try:
        expired_tokens = StudentRegistrationToken.objects.filter(expiry_date__lt = datetime.now())
        referer = request.META.get('HTTP_REFERER') or '/'
        if expired_tokens:
            deleted_count, _ = expired_tokens.delete()
            messages.success(request, f"Deleted {deleted_count} tokens.")
            
            AdminActionsLog.objects.create(
                action = "CLEAR",
                admin = request.user,
                victim_type = "EXPIRED STUDENT TOKENS",
                victim = f"{deleted_count} STUDENT REGISTRATION TOKENS"

            )
        else:
            messages.warning(request,"Nothing to be cleared")  
        return redirect(referer)
          
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)                  



@login_required
@user_passes_test(lambda u: u.is_superuser)
def verify_payment(request, pk):
    try:
        admin = request.user
        remarks = request.POST.get("remark")
        proof = get_object_or_404(PaymentProofVerification, id=pk)
        proof.remarks = remarks
        proof.admin = admin
        proof.status = "APPROVED"
        proof.save()
        
        messages.success(request, "Payment verified successfully")
        
        return redirect('admin_payment_proof')  # Replace with your actual URL name
        
    except Exception as e:
        messages.error(request, f"Error verifying payment: {str(e)}")
        return redirect('admin_payment_proof')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reject_payment(request, pk):
    try:
        admin = request.user
        remarks = request.POST.get("remark")
        if not remarks:
            messages.error(request, "Remarks are required for rejection")
            return redirect('admin_payment_proof')
            
        proof = get_object_or_404(PaymentProofVerification, id=pk)
        proof.remarks = remarks
        proof.admin = admin
        proof.status = "REJECTED"
        proof.save()
        
        messages.success(request, "Payment rejected successfully")

        return redirect('admin_payment_proof')
        
    except Exception as e:
        messages.error(request, f"Error rejecting payment: {str(e)}")
        return redirect('admin_payment_proof')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def send_invoice(request, pk):
    try:
        admin = request.user
        institution = get_object_or_404(Institution, id=pk)
        
        # generate token + login link
        token_data = generate_login_token(institution.email)
        token = token_data.get("token")
        expiry_date = token_data.get("expiry_date")

        InvoiceDownloadToken.objects.create(
            email=institution.email,
            token=token,
            expiry_date=expiry_date
        )
        print('done1')
        TransactionsLog.objects.create(
            admin = admin,
            action = "SEND",
            victim_type = "INVOICE",
            victim = f"{institution.email}"
        )
        print('done')
        return JsonResponse({"detail": "invoice sent"}, status=200)
    except Exception as e:
        messages.error(request, f"Error sending invoice: {str(e)}")
        return redirect("admin_deficits_view")
class ContactUsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = "administrator/admin_contactus.html"
    model = ContactUs
    login_url = reverse_lazy('adminLogin')
    context_object_name = "messages"
    
    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        # Order by newest first by default
        return ContactUs.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messages = context['messages']
        
        # Get category counts in a single query for better performance
        from django.db.models import Count
        category_counts_db = messages.values('category').annotate(count=Count('category'))
        
        # Convert to dictionary for easy lookup
        category_count_dict = {item['category']: item['count'] for item in category_counts_db}
        
        # Category configuration
        categories_config = [
            {"value": "business", "name": "Business Inquiry", "icon": "fas fa-briefcase", "badge_class": "bg-info"},
            {"value": "support", "name": "Support", "icon": "fas fa-headset", "badge_class": "bg-warning"},
            {"value": "bug", "name": "Bug Report", "icon": "fas fa-bug", "badge_class": "bg-danger"},
            {"value": "job", "name": "Job Request", "icon": "fas fa-user-tie", "badge_class": "bg-success"},
            {"value": "spam", "name": "Spam", "icon": "fas fa-ban", "badge_class": "bg-secondary"},
            {"value": "general", "name": "General", "icon": "fas fa-envelope", "badge_class": "bg-primary"},
        ]
        
        # Prepare category counts for summary
        category_counts = []
        categories = []
        
        for cat in categories_config:
            count = category_count_dict.get(cat["value"], 0)
            
            # For category summary (all categories shown even if 0)
            category_counts.append({
                "name": cat["name"],
                "count": count,
                "badge_class": cat["badge_class"]
            })
            
            # For template organization (all categories included)
            categories.append({
                "value": cat["value"],
                "name": cat["name"],
                "icon": cat["icon"],
                "badge_class": cat["badge_class"],
                "unread_count": count  # Note: This shows total count, unread will be handled by JavaScript
            })
        
        context['category_counts'] = category_counts
        context['categories'] = categories
        
        return context 

    

class DetailContactUsView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = ContactUs
    template_name = "administrator/contactus_detail.html"
    context_object_name = 'message'
    login_url = reverse_lazy('adminLogin')   

    def test_func(self):
       return self.request.user.is_superuser




class RegistrationTrackerView(LoginRequiredMixin,ListView,UserPassesTestMixin):
    template_name = 'administrator/admin_institution_registration_tracker.html'
    model = RegistrationTracker
    context_object_name = 'trackers'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser 

class SubmissionTrackerView(LoginRequiredMixin,ListView,UserPassesTestMixin):
    template_name = 'administrator/admin_student_registration_tracker.html'
    model = SubmissionTracker
    context_object_name = 'trackers'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser       

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only institutions actually connected to trackers, avoid useless dump
        context['unique_institutions'] = Institution.objects.all()
        return context
    

class InstitutionSignupTokenView(LoginRequiredMixin,ListView,UserPassesTestMixin):
    template_name = "administrator/admin_institution_signup.html"
    model = InstitutionSignupToken
    login_url = reverse_lazy('adminLogin')
    context_object_name = 'tokens'

    def test_func(self):
        return self.request.user.is_superuser
class InstitutionRegistrationTokenView(LoginRequiredMixin,ListView,UserPassesTestMixin):
    template_name = "administrator/admin_institution_registration.html"
    model = InstitutionRegistrationToken
    login_url = reverse_lazy('adminLogin')
    context_object_name = 'tokens'

    def test_func(self):
        return self.request.user.is_superuser
class DemoBookingView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = DemoBooking       
    template_name = 'administrator/admin_demobooking.html' 
    login_url = reverse_lazy('adminLogin')
    context_object_name = 'bookings'

    def test_func(self):
        return self.request.user.is_superuser

class DeleteDemoBooking(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = DemoBooking
    login_url = reverse_lazy('adminLogin')
    success_url = reverse_lazy('admin_demobooking')  

    def test_func(self):
        return self.request.user.is_superuser     

class CreateDemoBooking(LoginRequiredMixin,UserPassesTestMixin,CreateView):
    model = DemoBooking
    template_name = 'administrator/admin_create_demosession.html'        
    success_url = reverse_lazy('admin_demobooking') 
    login_url = reverse_lazy('adminLogin')
    fields = "__all__"

    def test_func(self):
        return self.request.user.is_superuser


class UpdateDemoBooking(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model = DemoBooking
    template_name = 'administrator/admin_reschedule_demo.html'
    success_url = reverse_lazy('admin_demobooking')
    context_object_name = 'demo'
    login_url = reverse_lazy('adminLogin')     
    fields = ['date','time']

    def test_func(self):
        return self.request.user.is_superuser

class DemoBookingDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = DemoBooking
    template_name = "administrator/admin_demosession_detail.html"
    login_url = reverse_lazy('adminLogin')
    context_object_name = 'session'

    def test_func(self):
        return self.request.user.is_superuser


class SignupTrackerView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = SignupTracker
    template_name = "administrator/admin_institution_signuptracker.html"
    context_object_name = 'trackers'

    def test_func(self):
        return self.request.user.is_superuser  

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # Only institutions actually connected to trackers, avoid useless dump
    #     context['institutions'] = Institution.objects.filter(
    #         signuptracker__isnull=False
    #     ).distinct().only('id','name')
    #     return context



class DemoBookingTrackerView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    template_name = 'administrator/admin_demobooking_tracker.html'
    model = DemoBookingTracker
    context_object_name = 'trackers'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser  

class ContactUsTrackerView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    template_name = 'administrator/admin_contactus_tracker.html'
    model = ContactUsTracker
    context_object_name = 'trackers'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser        


class DelteContactUsView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = ContactUs
    template_name = "administrator/contactus_confirm_delete.html"
    success_url = reverse_lazy("admin_contactus")
    login_url = reverse_lazy("adminLogin")

    def test_func(self):
        return self.request.user.is_superuser

class UserView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = User
    template_name = "administrator/admin_user_view.html"
    context_object_name = 'users'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser

class DeleteUserView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model = User
    login_url = reverse_lazy('adminLogin')
    def test_func(self):
        return self.request.user.is_superuser
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        return next_url 

class IssueView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = Issue
    template_name = "administrator/admin_issue_view.html"
    context_object_name = 'issues'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser

class IssueDetailView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
    model = Issue
    template_name = "administrator/admin_issue_detail.html"
    login_url = reverse_lazy('adminLogin')
    context_object_name = 'issue'

    def test_func(self):
        return self.request.user.is_superuser


class PaymentView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = Payment
    template_name = "administrator/admin_payment_view.html"
    context_object_name = 'payments'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['institutions'] = [deficit.institution for deficit in Deficits.objects.all() if deficit.amount]
        context['proofs'] = PaymentProofVerification.objects.filter(status="APPROVED").order_by("-created_at")
        return context   
            
class PaymentProofVerificationView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = PaymentProofVerification
    template_name="administrator/admin_payment_verification.html"
    context_object_name = "verifications"
    login_url = reverse_lazy('adminLogin')

    def test_func(self):
       return self.request.user.is_superuser  

class DeficitsView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = Deficits
    template_name="administrator/admin_deficits_view.html"
    context_object_name = "deficits"
    login_url = reverse_lazy('adminLogin')

    def test_func(self):
       return self.request.user.is_superuser   

    def get_context_data(self,*args,**kwargs) :        
        context = super().get_context_data(**kwargs)
        context['institutions'] = Institution.objects.all()
        return context

# class TransactionView(LoginRequiredMixin,UserPassesTestMixin,DetailView):
#     model = Transaction
#     template_name = "administrator/admin_transaction_view.html"
#     context_object_name = 'transaction'
#     login_url = reverse_lazy('adminLogin')    
#     def test_func(self):
#        return self.request.user.is_superuser 

class InstitutionLoginToken(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = InstitutionMagicLinkToken
    template_name = "administrator/admin_institution_login_token.html"
    context_object_name = 'tokens'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser   

class ReceiptDownloadTokenView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = PaymentReceiptDownloadToken
    template_name = "administrator/admin_receipt_download_tokens.html"
    context_object_name = 'tokens'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser  

class InvoiceDownloadTokenView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = InvoiceDownloadToken
    template_name = "administrator/admin_invoice_download_tokens.html"
    context_object_name = 'tokens'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser  

class LoginTrackerView(LoginRequiredMixin,UserPassesTestMixin,ListView):
    model = LoginTracker
    template_name = "administrator/admin_institution_login_tracker.html"
    context_object_name = 'trackers'
    login_url = reverse_lazy('adminLogin')    
    def test_func(self):
       return self.request.user.is_superuser 


class AdminRequiredMixin():
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    
class ExportToolView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    template_name = 'administrator/export_tool_view.html'
    login_url = reverse_lazy("adminLogin")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_tables'] = SchemaService.get_available_tables()
        context['institutions'] = Institution.objects.all().values('id', 'name')
        context['users'] = User.objects.all().values('id', 'username', 'email', 'first_name', 'last_name')
        return context

@method_decorator(csrf_exempt, name='dispatch')
class SchemaAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        table_name = request.GET.get('table')
        
        if table_name:
            schema = SchemaService.get_table_schema(table_name)
            if schema:
                return JsonResponse({'success': True, 'schema': schema})
            else:
                return JsonResponse({'success': False, 'error': 'Table not found'}, status=404)
        else:
            tables = SchemaService.get_available_tables()
            return JsonResponse({'success': True, 'tables': tables})

@method_decorator(csrf_exempt, name='dispatch')
class ExportAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        # Rate limiting
        cache_key = f"export_limit_{request.user.id}"
        export_count = cache.get(cache_key, 0)
        if export_count >= 10:  # Limit to 10 exports per minute
            return JsonResponse({'success': False, 'error': 'Rate limit exceeded. Please try again in a minute.'}, status=429)
        
        try:
            data = json.loads(request.body)
            
            table_name = data.get('table')
            columns = data.get('columns', [])
            filters = data.get('filters', {})
            format_type = data.get('format', 'csv')
            
            if not table_name:
                return JsonResponse({'success': False, 'error': 'Table parameter required'}, status=400)
            
            # Get model
            model = SchemaService.get_model_instance(table_name)
            if not model:
                return JsonResponse({'success': False, 'error': 'Invalid table'}, status=400)
            
            # Validate columns
            valid_columns = []
            for col in columns:
                try:
                    if '__' in col:
                        base_field = col.split('__')[0]
                        model._meta.get_field(base_field)
                    else:
                        model._meta.get_field(col)
                    valid_columns.append(col)
                except models.FieldDoesNotExist:
                    continue
            
            # Perform export
            response, record_count = ExportService.export_data(
                model, valid_columns, filters, format_type, request.user
            )
            
            # Log the export
            ExportLog.objects.create(
                user=request.user,
                table_name=table_name,
                columns_exported=json.dumps(valid_columns),
                filters_applied=json.dumps(filters),
                export_format=format_type,
                record_count=record_count,
                file_size=len(response.content),
                ip_address=self.get_client_ip(request)
            )
            
            # Update rate limit
            cache.set(cache_key, export_count + 1, 60)  # 1 minute timeout
            
            return response
            
        except ValueError as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Export failed: {str(e)}'}, status=500)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ExportLogsAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def get(self, request):
        try:
            page = int(request.GET.get('page', 1))
            per_page = int(request.GET.get('per_page', 50))
            
            start = (page - 1) * per_page
            end = start + per_page
            
            logs = ExportLog.objects.all().order_by('-created_at')[start:end]
            total_logs = ExportLog.objects.count()
            
            log_data = []
            for log in logs:
                log_data.append({
                    'id': log.id,
                    'user': log.user.username,
                    'table_name': log.table_name,
                    'export_format': log.export_format,
                    'record_count': log.record_count,
                    'file_size': self.format_file_size(log.file_size),
                    'created_at': log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'ip_address': log.ip_address,
                })
            
            return JsonResponse({
                'success': True, 
                'logs': log_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total_logs,
                    'pages': (total_logs + per_page - 1) // per_page
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    def format_file_size(self, size_bytes):
        """Convert file size to human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names)-1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"

class PreviewAPIView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            
            table_name = data.get('table')
            columns = data.get('columns', [])
            filters = data.get('filters', {})
            limit = data.get('limit', 20)
            
            if not table_name:
                return JsonResponse({'success': False, 'error': 'Table parameter required'}, status=400)
            
            model = SchemaService.get_model_instance(table_name)
            if not model:
                return JsonResponse({'success': False, 'error': 'Invalid table'}, status=400)
            
            # Apply filters and get limited results
            queryset = ExportService._apply_filters(model, filters)
            total_count = queryset.count()
            
            # Validate columns
            valid_columns = []
            for col in columns:
                try:
                    if '__' in col:
                        base_field = col.split('__')[0]
                        model._meta.get_field(base_field)
                    else:
                        model._meta.get_field(col)
                    valid_columns.append(col)
                except models.FieldDoesNotExist:
                    continue
            
            # Get preview data with valid columns only
            if valid_columns:
                preview_data = list(queryset.values(*valid_columns)[:limit])
            else:
                preview_data = list(queryset.values()[:limit])
            
            return JsonResponse({
                'success': True,
                'preview': preview_data,
                'total_count': total_count,
                'preview_count': len(preview_data)
            })
            
        except Exception as e:
            import traceback
            print(f"Preview error: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({'success': False, 'error': str(e)}, status=500)