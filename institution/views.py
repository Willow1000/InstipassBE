from student.serializers import StudentSerializer
from student.models import Student

from rest_framework.permissions import IsAuthenticated,IsAdminUser,AllowAny

from .models import *
from Id.models import *


from rest_framework.views import APIView

from .serializers import *
from django.shortcuts import get_object_or_404,redirect
import requests

import json
from django.contrib import messages

from rest_framework.parsers import MultiPartParser
from accounts.models import InstitutionSignupToken,InstitutionRegistrationToken,BannedIP
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import viewsets, status,parsers
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import DemoBooking
from administrator.models import DemoBookingTracker, ContactUsTracker
from .utils import *
from logs.models import AdminActionsLog,TransactionsLog
from .pagination import StudentCursorPagination
from django.db.models import Q
import pandas as pd
import os
import re
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from datetime import datetime

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

class InstitutionsViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionSerializer
    # permission_classes = [IsAdminUser]
    http_method_names = ['get']
    queryset = Institution.objects.all()

class InstitutionViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionSerializer
    http_method_names = ['get','post','put','patch','delete','options']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        institution = Institution.objects.filter(email = self.request.user.email)
        return institution

    # @method_decorator(ensure_csrf_cookie)
    # # def list(self, request):
    # #     # Optionally list all students (or just forbid)
    # #     return Response({"detail": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @method_decorator(ensure_csrf_cookie)
    def create(self, request):
        fingerprint = request.data.get('fingerprint')
        cookie_flag = request.COOKIES.get('form_submitted')

        # Block if fingerprint already submitted
        if fingerprint and RegistrationTracker.objects.filter(fingerprint=fingerprint).exists():
            return Response({"detail": "Already submitted with this device."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        # if RegistrationTracker.objects.filter(user_agent=request.META.get('HTTP_USER_AGENT', '')).exists():
        #     return Response({"detail": "Already submitted with this device."}, status=status.HTTP_403_FORBIDDEN)
        # Block if no fingerprint but cookie exists
        if cookie_flag:
            return Response({"detail": "Already submitted (cookie detected)."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = InstitutionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # Log submission tracker
            RegistrationTracker.objects.create(
                user = request.user,
                fingerprint=fingerprint or None,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            response = Response({"detail": "registration successful."}, status=status.HTTP_201_CREATED)
            response.set_cookie('form_submitted', 'true', max_age=60 * 60 * 24 * 365, httponly=True)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)     

class InstitutionSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionSettingsSerializer    
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'options']
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        institution = get_object_or_404(Institution, email=self.request.user.email)
        return InstitutionSettings.objects.filter(institution=institution)

    @method_decorator(ensure_csrf_cookie)
    def create(self, request):
        
        cookie_flag = request.COOKIES.get('form_submitted')

        # Block if fingerprint already submitted
       
        if cookie_flag:
            return Response({"detail": "Already submitted (cookie detected)."}, status=status.HTTP_403_FORBIDDEN)

        serializer = InstitutionSettingsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # Log submission tracker
            
            response = Response({"detail": "registration successful."}, status=status.HTTP_201_CREATED)
            response.set_cookie('form_submitted', 'true', max_age=60 * 60 * 24 * 365, httponly=True)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 
# from rest_framework import viewsets
# from rest_framework.response import Response

# from .models import InstitutionSettings
# from .serializers import InstitutionSettingsSerializer
# from .utils import decode_application_token  # assuming you placed the helper in utils.py


# from rest_framework import viewsets
# from rest_framework.exceptions import AuthenticationFailed
# from django.shortcuts import get_object_or_404
# from .models import InstitutionSettings, Institution
# from .serializers import InstitutionSettingsSerializer
# from .utils import decode_application_token


class InstitutionSettingsAllViewSet(viewsets.ModelViewSet):
    serializer_class = InstitutionSettingsSerializer
    http_method_names = ["get", "options"]
    # permission_classes = [AllowAny]

    def get_queryset(self):
        try:
            # Grab token from query params: ?token=xxxx
            token = self.request.query_params.get("token")
            if not token:
                raise AuthenticationFailed("Token is required.")

            decoded = decode_application_token(token)

            if not decoded.get("valid"):
                raise AuthenticationFailed(decoded.get("error", "Invalid token."))

            payload = decoded["payload"]
            institution_id = int(payload.get("institution_id"))
           

            institution = get_object_or_404(Institution, id=institution_id)
            return InstitutionSettings.objects.filter(institution=institution)

        except (AuthenticationFailed, ValidationError) as e:
            # These map to 400/401 errors
            print(f"[400 ERROR] {str(e)}")
            raise
        except Exception as e:
            # Unexpected issues still get logged
            print(f"[ERROR] Unexpected exception: {str(e)}")
            raise


class InstitutionStudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StudentCursorPagination
    http_method_names = ['get']

    def get_queryset(self):
        status = self.request.GET.get('status')
        name = self.request.GET.get('search')
        reg = self.request.GET.get('reg_no')
        print(status)
        institution = get_object_or_404(Institution,email = self.request.user.email)
        if reg:
            return Student.objects.filter(institution=institution,reg_no__icontains=reg).order_by('-created_at')

        elif status and name:
            return Student.objects.filter(
                Q(institution=institution),
                Q(status=status),
                Q(first_name=name) | Q(last_name=name)
            ).order_by('-created_at')

        elif status:
            return Student.objects.filter(institution=institution,status=status).order_by('-created_at')

        elif name:
            return Student.objects.filter(
                Q(institution=institution),
                Q(first_name__icontains=name) | Q(last_name__icontains=name)
            ).order_by('-created_at')
        
        students = Student.objects.filter(institution=institution).order_by('-created_at')
        return students

class IdProcessStatsAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request, *args, **kwargs):
        email=self.request.GET.get("q")
        institution = get_object_or_404(Institution,email = email)
        try: 
            expected_total = InstitutionSettings.objects.filter(institution=institution).first().expected_total
        except:
            expected_total=0    
        data = {
            "registered_students": Student.objects.filter(institution=institution).count(),
            # "Ids_being_processed": Student.objects.filter(institution=institution,status='id_processing').count(),
            "Ids_ready": Student.objects.filter(institution=institution,status='id_ready').count(),
            "expected":  expected_total
        }
        
        return Response(data=data)

class StudentRegistrationAPIView(APIView):
    # permission_classes=[IsAuthenticated]
    def post(self, request, *args, **kwargs):
        # Step 1: Extract token from the JSON body
        token = request.data.get('token')

        if not token:
            return Response({'detail': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Decode the token
           
        response = decode_application_token(token)

        # Step 3: Handle different cases

        if response.get("error") == 'Token expired':
            return Response({'detail': 'Token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)

        elif response.get("error") == 'Invalid Token':
            return Response({'detail': 'Token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)

        elif response.get('valid'):
            # Assume the decoded response contains institution_id or some valid payload
            institution_id = response.get('payload').get("institution_id")

            if institution_id:
                return Response({'institution_id': institution_id}, status=status.HTTP_200_OK) 
            else:
                return  Response({'detail':"Token is valid"}, status=status.HTTP_200_OK) 

    

        return Response({'detail': 'Token does not exist'}, status=status.HTTP_400_BAD_REQUEST)
class CreateInstitutionSignupTokenAPIView(APIView):
    permission_classes=[IsAuthenticated,IsAdminUser]
    def post(self,request, *args, **kwargs):
        email = request.data.get('email')            
        if not email:
            return Response({'detail': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Decode the token
        token_obj = generate_signup_token(email)
        expiry_date = token_obj.get("expiry_date")
        token = token_obj.get("token")
        InstitutionSignupToken.objects.create(
            email=email,
            token = token,
            expiry_date = expiry_date
        )
        AdminActionsLog.objects.create(
            action = "CREATE",
            admin = request.user,
            victim_type = "USERSIGNNUPTOKEN",
            victim = f"{email}: {token}"

        )
        response = Response({'detail': 'Token created sucssessfully.'}, status=status.HTTP_201_CREATED)
        return response

class CreateInstitutionLoginTokenAPIView(APIView):
    permission_classes=[IsAuthenticated,IsAdminUser]
    def post(self,request, *args, **kwargs):
        email = request.data.get('email')            
        if not email:
            return Response({'detail': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        institution = get_object_or_404(Institution,email=email)

        # Step 2: Decode the token
        token_obj = generate_login_token(email)
        token = token_obj.get('token')
        expiry = token_obj.get("expiry_date")
        lifetime = token_obj.get("lifetime")
        InstitutionMagicLinkToken.objects.create(
            institution = institution,
            token = token,
            expiry_date = expiry,
            
        )
        AdminActionsLog.objects.create(
            action = "CREATE",
            admin = request.user,
            victim_type = "INSTITUTIONLOGINTOKEN",
            victim = f"{institution}: {token}"

        )
        
        response = Response({'detail': 'Token created sucssessfully.'}, status=status.HTTP_201_CREATED)
        return response
# class DecodeSignupTokenAPIView(APIView):
#     permission_classes=[IsAuthenticated]
#     def post(self,request, *args, **kwargs):
        # Step 1: Extract token from the JSON body
        # token = request.data.get('token')

        # if not token:
        #     return Response({'detail': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # # Step 2: Decode the token
        # response = decode_application_token(token)

        # # Step 3: Handle different cases
        # if response == 'Token expired':
        #     return Response({'detail': 'Token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)

        # elif response == 'Token invalid':
        #     return Response({'detail': 'Token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)

        # elif type(response) == 'dict':
        #     # Assume the decoded response contains institution_id or some valid payload
        #     institution_id = response.get('institution_id')
        #     return Response({'institution_id': institution_id,'institution':institution}, status=status.HTTP_200_OK)   
        # else:
        #     return Response({'detail': 'Token is invalid.'}, status=status.HTTP_400_BAD_REQUEST)

class CreateInstitutionRegistrationTokenAPIView(APIView):
    permission_classes=[IsAuthenticated,IsAdminUser]
    def post(self,request, *args, **kwargs):
        email = request.data.get('email')            
        if not email:
            return Response({'detail': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User,email=email)
        # Step 2: Decode the token
        token_obj = generate_signup_token(email)
        token = token_obj.get('token')
        expiry_date = token_obj.get("expiry_date")
        InstitutionRegistrationToken.objects.create(
            user=user,
            token = token,
            expiry_date = expiry_date
        )
        AdminActionsLog.objects.create(
            action = "CREATE",
            admin = request.user,
            victim_type = "INSTITUTIONREGISTRATIONTOKEN",
            victim = f"{user}: {token}"

        )
        response = Response({'detail': 'Token created sucssessfully.'}, status=status.HTTP_201_CREATED)
        return response


class CreateStudentRegistrationTokenAPIView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request, *args, **kwargs):
        email = request.data.get('email')            
        if not email:
            return Response({'detail': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        institution = get_object_or_404(Institution,email=email)
        match = StudentRegistrationToken.objects.filter(institution=institution).count()
        if match >= 2:
            return Response({'detail': 'token request exceeded'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        # Step 2: Decode the token
        token_obj = generate_student_registration_token(institution)
        token = token_obj.get('token')
        expiry = token_obj.get("expiry_date")
        lifetime = token_obj.get("lifetime")
        StudentRegistrationToken.objects.create(
            institution = institution,
            token = token,
            expiry_date = expiry,
            lifetime = lifetime
        )
        AdminActionsLog.objects.create(
            action = "CREATE",
            admin = request.user,
            victim_type = "STUDENTSIGNUPTOKEN",
            victim = f"{institution}: {token}"

        )
        
        response = Response({'detail': 'Token created sucssessfully.'}, status=status.HTTP_201_CREATED)
        return response
class DeficitsViewSet(viewsets.ModelViewSet):
    serializer_class=DeficitsSerializer
    http_method_names=['get']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        email = self.request.user.email
        institution = get_object_or_404(Institution,email=email)
        if Deficits.objects.filter(institution=institution).last():
            deficit = Deficits.objects.filter(institution=institution).last()
            return [deficit]
        return []    


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    http_method_names = ['get','post']
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        institution = get_object_or_404(Institution,email = self.request.user.email)
        return Notifications.objects.filter(recipient = institution)
    
class ConfirmDemo(APIView):
    def get(self, request, *args, **kwargs):
        id = self.request.GET.get("pk")  
        if not id:
            return Response({'detail':'pk is required'},status=status.HTTP_400_BAD_REQUEST)
        demo = DemoBooking.objects.filter(id = id)    
        if demo.exists():
            demo_obj = demo.last()
            if demo_obj.status == 'CONFIRMED':
                return Response({'detail':'session is already confirmed'},status=status.HTTP_409_CONFLICT)
            demo_obj.status = 'CONFIRMED' 
            demo_obj.save()
            return Response({'detail':"Demo session confirmed"}, status=status.HTTP_200_OK)
        else:
            message.warning(self.request,"record does not exist")
            return Response({'detail':'Demo session does not exist'},status=status.HTTP_404_NOT_FOUND)    

class NewsLetterViewSet(viewsets.ModelViewSet):
    queryset = NewsLetter.objects.all()
    serializer_class = NewsLetterSerializer
    http_method_names = ['post']

class NotificationsViewSet(viewsets.ModelViewSet):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer
    http_method_names = ['post']
    @method_decorator(ensure_csrf_cookie)
    def create(self, request):
        fingerprint = request.data.get('fingerprint')
        ip_address = get_client_ip(request)
        cookie_flag = request.COOKIES.get('contactus_form_submitted')

        if cookie_flag:
            return Response({"detail": "Limit Reached"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        # Block if fingerprint already submitted
        if (fingerprint and ContactUsTracker.objects.filter(fingerprint=fingerprint).count() >= 10) or ContactUsTracker.objects.filter(ip_address=ip_address).count() >= 10:
                
                response = Response({"detail": "Limit reached"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
                # Set cookie (valid for 1 year)
                expires = timezone.now() + timedelta(days=365)
                response.set_cookie(
                    key='contactus_form_submitted',
                    value='true',
                    expires=expires,
                    secure=True,          # Only over HTTPS
                    samesite='Lax',
                    path='/'
                )
                banned_ip = BannedIP.objects.filter(ip_address=ip_address).last()
                if banned_ip:
                    banned_ip.extend_ban()
                else:
                    BannedIP.objects.create(
                        ip_address=ip_address,
                        banned_until=timezone.now() + timedelta(days=365),
                        reason="Exceeded demo booking limit"  # optional
                    )
                return response


        # Block if no fingerprint but cookie exists
        

        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            # print(serializer.is_valid())
            serializer.save()
            # Log submission tracker
            ContactUsTracker.objects.create(
                fingerprint=fingerprint or None,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            response = Response({"detail": "Message successfully."}, status=status.HTTP_201_CREATED)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)     
       

class DemoBookingViewSet(viewsets.ModelViewSet):
    queryset = DemoBooking.objects.all()
    serializer_class = DemoBookingSerializer
    http_method_names=['post','get']
    @method_decorator(ensure_csrf_cookie)
    def create(self, request):
        fingerprint = request.data.get('fingerprint')
        ip_address = get_client_ip(request)
        cookie_flag = request.COOKIES.get('demo_form_submitted')
        # Block if fingerprint already submitted

        if cookie_flag:
            return Response({"detail": "Limit Reached"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        if (fingerprint and DemoBookingTracker.objects.filter(fingerprint=fingerprint).count() >= 10) or DemoBookingTracker.objects.filter(ip_address=ip_address).count() >= 10:
                
                response = Response({"detail": "Limit reached"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
                # Set cookie (valid for 1 year)
                expires = timezone.now() + timedelta(days=365)
                response.set_cookie(
                    key='demo_form_submitted',
                    value='true',
                    expires=expires,
                    secure=True,          # Only over HTTPS
                    samesite='Lax',
                    path='/'
                )
                banned_ip = BannedIP.objects.filter(ip_address=ip_address).last()

                if banned_ip:
                    banned_ip.extend_ban()
                else:
                    BannedIP.objects.create(
                        ip_address=ip_address,
                        banned_until=timezone.now() + timedelta(days=365),
                        reason="Exceeded demo booking limit"  # optional
                    )
                return response

        # Block if no fingerprint but cookie exists
        

        serializer = DemoBookingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # Log submission tracker
            DemoBookingTracker.objects.create(
                fingerprint=fingerprint or None,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            response = Response({"detail": "Demo sessioin booked successfuly"}, status=status.HTTP_201_CREATED)
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    

class IssueViewSet(viewsets.ModelViewSet):
    serializer_class = IssueSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

class TestimonialViewSet(viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    serializer_class = TestimonialSerializer
    # permission_classes = [IsAuthenticated]
    http_method_names = ['post','get','options']    

class PaymentAPIView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    http_method_names = ['post']
    # def get(self, request):
    #     """Return all payments for the institution of the authenticated user"""
    #     institution = get_object_or_404(Institution, email=request.user.email)
    #     payments = Payment.objects.filter(institution=institution)
    #     serializer = PaymentSerializer(payments, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a payment and log it if the user is an admin"""
        # institution = get_object_or_404(Institution, email=request.user.email)
        data = request.data.copy()
        # data["institution"] = institution.id  # attach institution

        serializer = PaymentSerializer(data=data)
        if serializer.is_valid():
            payment = serializer.save()
            institution = payment.institution
            deficit = Deficits.objects.filter(institution=institution).last()
            if deficit:
                if deficit.amount:
                    deficit.amount-=payment.amount
                    deficit.save()
                else:
                    return Response({'detail': 'Balance must not be 0.00'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                    return Response({'detail': 'Deficit must exist for payment to be made.'}, status=status.HTTP_400_BAD_REQUEST)        
            # ✅ Log the transaction if user is admin
            if request.user.is_staff or request.user.is_superuser:
                TransactionsLog.objects.create(
                    admin=request.user,
                    action="CREATE",
                    victim_type = "PAYMENT",
                    victim = f"{payment}"
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeficitsAPIView(APIView):
    permission_classes = [IsAuthenticated,IsAdminUser]
    http_method_names = ['post']
    # def get(self, request):
    #     """Return all payments for the institution of the authenticated user"""
    #     institution = get_object_or_404(Institution, email=request.user.email)
    #     payments = Payment.objects.filter(institution=institution)
    #     serializer = PaymentSerializer(payments, many=True)
    #     return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a payment and log it if the user is an admin"""
        # institution = get_object_or_404(Institution, email=request.user.email)
        data = request.data.copy()
        # data["institution"] = institution.id  # attach institution

        serializer = DeficitsSerializer(data=data)
        if serializer.is_valid():
            deficit = serializer.save()
            
            # ✅ Log the transaction if user is admin
            if request.user.is_staff or request.user.is_superuser:
                TransactionsLog.objects.create(
                    admin=request.user,
                    action="CREATE",
                    victim_type = "DEFICIT",
                    victim = f"{deficit}"
                )

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentProofVerificationViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentProofVerificationSerializer
    permission_classes=[IsAuthenticated]
    http_method_names = ['post','update','options']  

# views.py

# import logging

# logger = logging.getLogger(__name__)

def download_receipt(request):
    token = request.GET.get("token")  
    

    if not token:
        return Response({'detail': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    token_obj= PaymentReceiptDownloadToken.objects.filter(token=token).last()

    if token_obj:
    # Step 2: Decode the token
        if token_obj.used:
            return HttpResponse("Link can only be used once", status=403)
        response = decode_application_token(token)

        # Step 3: Handle different cases
        if response == 'Token expired':
            return Response({'detail': 'Token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)

        elif response == 'Token invalid':
            return Response({'detail': 'Token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        # fetch payment from DB if real project
        # print(response)
        email = response.get("payload").get('target')
        institution = get_object_or_404(Institution,email=email)
        payment = Payment.objects.filter(institution=institution).last()
        deficit = Deficits.objects.filter(institution=institution).last()
        balance = deficit.amount
        receipt_data = {
            "company_name": "Instipass Ltd",
            "reference_number": payment.reference_number,
            "receipt_id": payment.id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "customer_name": institution.name,
            "customer_email": institution.email,
            "amount": payment.amount,  # Formatted with commas
            "currency": payment.currency,
            "payment_method": payment.method,
            "balance": balance,
            "year": datetime.now().year,
        }

        html_string = render_to_string('emailtemplates/receipt.html', receipt_data)
        
        # Create PDF with additional options
        pdf_file = HTML(
            string=html_string,
            base_url=request.build_absolute_uri()
        ).write_pdf()
        token_obj.used=True
        token_obj.save()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{institution.name}_receipt_{payment.id}.pdf"'
        return response
        
    except Exception as e:
        # logger.error(f"Error generating receipt: {str(e)}")
        return HttpResponse(f"Error generating receipt {e}", status=500)


from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import logging

# Set up logger


def download_invoice(request):
    """
    Download invoice PDF using a secure token
    """
    # Validate token
    token = request.GET.get("token")  
    if not token:

        return JsonResponse({'detail': 'Download token is required.'}, status=400)
    
    try:
        # Get token object
        token_obj = InvoiceDownloadToken.objects.filter(token=token).first()
        if not token_obj:
           
            return JsonResponse({'detail': 'Invalid download token.'}, status=401)

        # Check if token has been used
        if token_obj.used:
            
            return JsonResponse({'detail': 'This download link has already been used.'}, status=403)

        # Check token expiration
        if token_obj.expiry_date and token_obj.expiry_date < timezone.now():
           
            return JsonResponse({'detail': 'Download link has expired.'}, status=401)

        # Validate token
        response = decode_application_token(token)
        if response.get("error"):
            error_msg = response.get("error")
            
            return JsonResponse({'detail': f'Download token error: {error_msg}.'}, status=401)

        # Extract data from token
        payload = response.get("payload", {})
        email = payload.get('target')
        if not email:
    
            return JsonResponse({'detail': 'Invalid token payload.'}, status=401)

        # Get institution and related objects
        institution = get_object_or_404(Institution, email=email)
        
        # Get latest payment
        payment = Payment.objects.filter(institution=institution).last()
        if not payment:

            return JsonResponse({'detail': 'No payment record found.'}, status=404)

        # Get latest deficit
        deficit = Deficits.objects.filter(institution=institution).last()
        if not deficit:

            return JsonResponse({'detail': 'No outstanding deficit found.'}, status=404)

        # Prepare invoice data
        invoice_data = {
            "company_name": "Instipass Ltd",
            "company_address": "Your Company Address",  # Add company details
            "company_phone": "+1234567890",  # Add contact info
            "company_email": "billing@instipass.com",
            "invoice_number": f"INV-{deficit.id}",
            "invoice_id": token_obj.id,
            "date_issued": timezone.now().strftime("%Y-%m-%d"),
            "due_date": (timezone.now() + timezone.timedelta(days=30)).strftime("%Y-%m-%d"),  # 30 days due
            "customer_name": institution.name,
            "customer_email": institution.email,
            "customer_address": getattr(institution, 'address', 'N/A'),  # Add address if available
            "amount_due": deficit.amount,
            "currency": "KES",  # Add currency
            "payment_terms": "Net 30",  # Add payment terms
            "items": [  # Add line items
                {
                    "description": f"{deficit.get_type_display()} - {institution.name}",
                    "quantity": 1,
                    "unit_price": deficit.amount,
                    "total": deficit.amount
                }
            ],
            "subtotal": deficit.amount,
            "tax_rate": 0.0,  # Add tax if applicable
            "tax_amount": 0.0,
            "total": deficit.amount,
            "year": timezone.now().year,
            "notes": "Thank you for your business!",  # Add notes
            "terms": "Payment due within 30 days. Late fees may apply."  # Add terms
        }

        # Generate PDF
        try:
            html_string = render_to_string('emailtemplates/invoice.html', invoice_data)
            pdf_file = HTML(
                string=html_string, 
                base_url=request.build_absolute_uri()
            ).write_pdf()
        except Exception as pdf_error:
   
            return JsonResponse({'detail': 'Failed to generate invoice PDF.'}, status=500)

        # Mark token as used
        token_obj.used = True
        token_obj.used_at = timezone.now()
        token_obj.save()

        # Log successful download


        # Return PDF response
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{institution.name}_invoice_{payment.reference_number}.pdf"'
        response['X-Frame-Options'] = 'SAMEORIGIN'  # Security header
        return response

    except Institution.DoesNotExist:

        return JsonResponse({'detail': 'Institution not found.'}, status=404)
    
    except Exception as e:

        return JsonResponse({'detail': f'An unexpected error occurred while generating the invoice. {e}'}, status=500)
class StudentVerificationView(APIView):
    # permission_classes=[IsAuthenticated]
    def post(self, request, *args, **kwargs):
        token = request.GET.get('token')

        if not token:
            return Response({'detail': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Decode the token
           
        response = decode_application_token(token)

        # Step 3: Handle different cases

        if response.get("error") == 'Token expired':
            return Response({'detail': 'Token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)

        elif response.get("error") == 'Invalid Token':
            return Response({'detail': 'Token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)
        elif not response.get("payload").get("institution_id"):
            return Response({'detail': 'Token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)
        # Extract required data from request
        registration_no = request.data.get('registration_no')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        institution_id = request.data.get('institution_id')
        
        # Validate required fields
        if not all([registration_no, email, phone_number, institution_id]):
            error_msg = 'All fields are required'
            print(f"ERROR: {error_msg}")
            return Response(
                {'error': error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ensure phone_number is treated as string
        phone_number = str(phone_number) if phone_number is not None else ""
        
        try:
            # Get institution settings
            token = self.request.query_params.get("token")
           
            if not token:
                raise AuthenticationFailed("Token is required.")

            decoded = decode_application_token(token)

            if not decoded.get("valid"):
                raise AuthenticationFailed(decoded.get("error", "Invalid token."))
            
            institution = get_object_or_404(Institution, id=institution_id)
            institution_settings = InstitutionSettings.objects.get(institution=institution)
            
            # Return null immediately if no conf_data file exists
            if not institution_settings.conf_data:
                print("ERROR: No configuration data file found")
                return Response({'exists': None}, status=status.HTTP_200_OK)
            
            # Check if file exists physically
            if not default_storage.exists(institution_settings.conf_data.name):
                print("ERROR: Configuration data file does not exist physically")
                return Response({'exists': None}, status=status.HTTP_200_OK)
            
            # Get the file path
            file_path = institution_settings.conf_data.path
            
            # Determine file type and read data
            file_name = institution_settings.conf_data.name
            file_extension = os.path.splitext(file_name)[1].lower()
            
            student_exists = False
            mismatch_details = []
            
            if file_extension == '.json':
                student_exists, mismatch_details = self._check_json_file(file_path, registration_no, email, phone_number)
            elif file_extension in ['.xlsx', '.xls']:
                student_exists, mismatch_details = self._check_excel_file(file_path, registration_no, email, phone_number)
            elif file_extension == '.csv':
                student_exists, mismatch_details = self._check_csv_file(file_path, registration_no, email, phone_number)
            else:
                # Unsupported format, return null
                print(f"ERROR: Unsupported file format: {file_extension}")
                return Response({'exists': None}, status=status.HTTP_200_OK)
            
            # Print mismatch details if student not found
            if not student_exists and mismatch_details:
                print("MISMATCH DETAILS:")
                for detail in mismatch_details:
                    print(f"  - {detail}")
            
            # Return true/false based on match
            return Response({'exists': student_exists}, status=status.HTTP_200_OK)
            
        except ObjectDoesNotExist as e:
            error_msg = f'Institution not found: {str(e)}'
            print(f"ERROR: {error_msg}")
            return Response(
                {'error': error_msg},
                status=status.HTTP_404_NOT_FOUND
            )
        except AuthenticationFailed as e:
            error_msg = f'Authentication failed: {str(e)}'
            print(f"ERROR: {error_msg}")
            return Response(
                {'error': error_msg},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            # Return null for any processing errors
            error_msg = f"Processing error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return Response({'exists': None}, status=status.HTTP_200_OK)
    
    def _normalize_phone_number(self, phone_number):
        """Normalize phone number for comparison, handling +254 and other formats"""
        if not phone_number:
            return ""
        
        # Convert to string and strip
        phone_str = str(phone_number).strip()
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone_str)
        
        # Handle Kenyan phone number formats
        if phone_str.startswith('+'):
            return phone_str
        elif len(cleaned) == 10 and cleaned.startswith('0'):
            return '+254' + cleaned[1:]
        elif len(cleaned) == 9:
            return '+254' + cleaned
        elif len(cleaned) == 12 and cleaned.startswith('254'):
            return '+' + cleaned
        
        return phone_str
    
    def _check_json_file(self, file_path, registration_no, email, phone_number):
        """Check student existence in JSON file and return match status with mismatch details"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            students = []
            if isinstance(data, list):
                students = data
            elif isinstance(data, dict):
                possible_keys = ['students', 'data', 'records', 'users', 'student_data', 'members']
                for key in possible_keys:
                    if key in data and isinstance(data[key], list):
                        students = data[key]
                        break
                if not students:
                    students = []
                    for key, value in data.items():
                        if isinstance(value, list):
                            students.extend(value)
                        elif isinstance(value, dict):
                            students.append(value)
                    if not students:
                        students = [data]
            else:
                students = []
            
            mismatch_details = []
            
            for student in students:
                if isinstance(student, dict):
                    match_result, details = self._match_student_record(student, registration_no, email, phone_number)
                    if match_result:
                        return True, []
                    else:
                        if details:
                            mismatch_details.extend(details)
                else:
                    mismatch_details.append("Invalid record format")
            
            if not students:
                mismatch_details.append("No student records found in JSON file")
            
            return False, mismatch_details
            
        except Exception as e:
            error_msg = f"JSON file processing error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return False, [error_msg]
    
    def _check_excel_file(self, file_path, registration_no, email, phone_number):
        """Check student existence in Excel file and return match status with mismatch details"""
        try:
            df = pd.read_excel(file_path)
            return self._check_dataframe(df, registration_no, email, phone_number, "Excel")
        except Exception as e:
            error_msg = f"Excel file processing error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return False, [error_msg]
    
    def _check_csv_file(self, file_path, registration_no, email, phone_number):
        """Check student existence in CSV file and return match status with mismatch details"""
        try:
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'windows-1252']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                error_msg = "CSV file: Could not decode with any encoding"
                print(f"ERROR: {error_msg}")
                return False, [error_msg]
                
            return self._check_dataframe(df, registration_no, email, phone_number, "CSV")
        except Exception as e:
            error_msg = f"CSV file processing error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return False, [error_msg]
    
    def _check_dataframe(self, df, registration_no, email, phone_number, file_type="file"):
        """Check student existence in pandas DataFrame and return match status with mismatch details"""
        try:
            if df.empty:
                error_msg = f"{file_type} file: DataFrame is empty"
                print(f"ERROR: {error_msg}")
                return False, [error_msg]
            
            df_normalized = self._normalize_column_names(df)
            if df_normalized is None:
                error_msg = f"{file_type} file: Column normalization failed"
                print(f"ERROR: {error_msg}")
                return False, [error_msg]
            
            required_columns = ['registration_no', 'email', 'phone_number']
            available_columns = set(df_normalized.columns)
            
            missing_columns = [col for col in required_columns if col not in available_columns]
            if missing_columns:
                error_msg = f"{file_type} file: Missing required columns: {', '.join(missing_columns)}"
                print(f"ERROR: {error_msg}")
                return False, [error_msg]
            
            df_clean = df_normalized.copy()
            df_clean = df_clean.dropna(subset=required_columns)
            
            # Convert all fields to string and strip whitespace
            for col in required_columns:
                df_clean[col] = df_clean[col].astype(str).str.strip()
            
            df_clean['email'] = df_clean['email'].str.lower()
            
            # Normalize phone numbers in the dataframe
            df_clean['phone_number'] = df_clean['phone_number'].apply(self._normalize_phone_number)
            
            # Clean input data
            registration_no_clean = str(registration_no).strip()
            email_clean = str(email).strip().lower()
            phone_number_clean = self._normalize_phone_number(phone_number)
            
            # Check for exact matches
            exact_match_conditions = (
                (df_clean['registration_no'] == registration_no_clean) &
                (df_clean['email'] == email_clean) &
                (df_clean['phone_number'] == phone_number_clean)
            )
            
            exact_matches = df_clean[exact_match_conditions]
            if not exact_matches.empty:
                return True, []
            
            # If no exact match found, collect detailed mismatch information
            mismatch_details = []
            
            # Check individual field matches to provide specific feedback
            reg_matches = df_clean[df_clean['registration_no'] == registration_no_clean]
            email_matches = df_clean[df_clean['email'] == email_clean]
            phone_matches = df_clean[df_clean['phone_number'] == phone_number_clean]
            
            if reg_matches.empty:
                mismatch_details.append(f"Registration number '{registration_no_clean}' not found")
            else:
                mismatch_details.append(f"Registration number found but email/phone don't match")
                
            if email_matches.empty:
                mismatch_details.append(f"Email '{email_clean}' not found")
            else:
                mismatch_details.append(f"Email found but registration/phone don't match")
                
            if phone_matches.empty:
                mismatch_details.append(f"Phone number '{phone_number_clean}' not found")
            else:
                mismatch_details.append(f"Phone number found but registration/email don't match")
            
            return False, mismatch_details
            
        except Exception as e:
            error_msg = f"{file_type} file DataFrame processing error: {str(e)}"
            print(f"ERROR: {error_msg}")
            return False, [error_msg]
    
    def _match_student_record(self, student_record, registration_no, email, phone_number):
        """Check if student record matches the provided details and return mismatch details"""
        try:
            if not student_record or not isinstance(student_record, dict):
                return False, ["Invalid student record format"]
            
            reg_aliases = [
                'registration no', 'reg no', 'registration number', 'student id', 
                'reg number', 'student no', 'student number', 'admission no',
                'admission number', 'roll no', 'roll number', 'matric no',
                'matric number', 'registration_no', 'reg_no', 'registration_number', 
                'student_id', 'id', 'studentid', 'reg_number', 'registration', 
                'student_no', 'student_number', 'regno', 'studentno', 'adm_no', 
                'admission_no', 'admission_number', 'roll_no', 'roll_number', 
                'rollno', 'matric_no', 'matric_number'
            ]
            
            email_aliases = [
                'email', 'email address', 'student email', 'mail', 'email id', 
                'electronic mail', 'contact email', 'mail id', 'email address',
                'email_address', 'student_email', 'email_id', 'e_mail', 'emailid',
                'electronic_mail', 'contact_email', 'mail_id', 'e-mail'
            ]
            
            phone_aliases = [
                'phone number', 'phone', 'mobile', 'contact number', 'phone no', 
                'mobile number', 'contact', 'tel', 'telephone', 'phone num',
                'mobile no', 'contact phone', 'telephone number', 'cell number',
                'cell phone', 'mobile no', 'contact no', 'telephone no',
                'phone_number', 'phone_no', 'mobile_number', 'contact_number', 
                'phone_num', 'mobile_no', 'contact_phone', 'telephone_number', 
                'cell_number', 'cell_phone', 'phonenumber', 'mobileno', 
                'contactno', 'telephoneno'
            ]
            
            reg_value = self._extract_field_value(student_record, reg_aliases)
            email_value = self._extract_field_value(student_record, email_aliases)
            phone_value = self._extract_field_value(student_record, phone_aliases)
            
            if not all([reg_value, email_value, phone_value]):
                missing_fields = []
                if not reg_value: missing_fields.append("registration number")
                if not email_value: missing_fields.append("email")
                if not phone_value: missing_fields.append("phone number")
                return False, [f"Missing fields in record: {', '.join(missing_fields)}"]
            
            reg_value_clean = reg_value.strip()
            email_value_clean = email_value.strip().lower()
            phone_value_clean = self._normalize_phone_number(phone_value)
            
            registration_no_clean = str(registration_no).strip()
            email_clean = str(email).strip().lower()
            phone_number_clean = self._normalize_phone_number(phone_number)
            
            reg_match = reg_value_clean == registration_no_clean
            email_match = email_value_clean == email_clean
            phone_match = phone_value_clean == phone_number_clean
            
            if reg_match and email_match and phone_match:
                return True, []
            
            # Collect mismatch details
            mismatch_details = []
            if not reg_match:
                mismatch_details.append(f"Registration number mismatch: expected '{registration_no_clean}', found '{reg_value_clean}'")
            if not email_match:
                mismatch_details.append(f"Email mismatch: expected '{email_clean}', found '{email_value_clean}'")
            if not phone_match:
                mismatch_details.append(f"Phone number mismatch: expected '{phone_number_clean}', found '{phone_value_clean}'")
            
            return False, mismatch_details
            
        except Exception as e:
            error_msg = f"Record matching error: {str(e)}"
            return False, [error_msg]

    def _normalize_column_names(self, df):
        """Normalize column names by detecting various naming patterns and cases"""
        try:
            original_columns = df.columns.tolist()
            lower_columns = [str(col).lower() for col in original_columns]
            
            column_aliases = {
                'registration_no': [
                    'registration no', 'reg no', 'registration number', 'student id', 
                    'reg number', 'student no', 'student number', 'admission no',
                    'admission number', 'roll no', 'roll number', 'matric no',
                    'matric number', 'registration_no', 'reg_no', 'registration_number', 
                    'student_id', 'id', 'studentid', 'reg_number', 'registration', 
                    'student_no', 'student_number', 'regno', 'studentno', 'adm_no', 
                    'admission_no', 'admission_number', 'roll_no', 'roll_number', 
                    'rollno', 'matric_no', 'matric_number'
                ],
                'email': [
                    'email', 'email address', 'student email', 'mail', 'email id', 
                    'electronic mail', 'contact email', 'mail id', 'email address',
                    'email_address', 'student_email', 'email_id', 'e_mail', 'emailid',
                    'electronic_mail', 'contact_email', 'mail_id', 'e-mail'
                ],
                'phone_number': [
                    'phone number', 'phone', 'mobile', 'contact number', 'phone no', 
                    'mobile number', 'contact', 'tel', 'telephone', 'phone num',
                    'mobile no', 'contact phone', 'telephone number', 'cell number',
                    'cell phone', 'mobile no', 'contact no', 'telephone no',
                    'phone_number', 'phone_no', 'mobile_number', 'contact_number', 
                    'phone_num', 'mobile_no', 'contact_phone', 'telephone_number', 
                    'cell_number', 'cell_phone', 'phonenumber', 'mobileno', 
                    'contactno', 'telephoneno'
                ]
            }
            
            column_mapping = {}
            
            for standard_name, aliases in column_aliases.items():
                for alias in aliases:
                    alias_lower = alias.lower()
                    if alias_lower in lower_columns:
                        idx = lower_columns.index(alias_lower)
                        original_col = original_columns[idx]
                        column_mapping[original_col] = standard_name
                        break
                    else:
                        for i, col_lower in enumerate(lower_columns):
                            clean_alias = re.sub(r'[^a-z0-9]', '', alias_lower)
                            clean_col = re.sub(r'[^a-z0-9]', '', col_lower)
                            if clean_alias == clean_col:
                                original_col = original_columns[i]
                                column_mapping[original_col] = standard_name
                                break
            
            if column_mapping:
                return df.rename(columns=column_mapping)
            else:
                return df
                
        except Exception as e:
            print(f"ERROR in _normalize_column_names: {str(e)}")
            return None

    def _find_matching_key(self, record, possible_keys):
        """Find a key in a dictionary using case-insensitive matching"""
        if not record:
            return None
            
        record_lower = {str(k).lower(): k for k in record.keys()}
        
        for key in possible_keys:
            key_lower = key.lower()
            if key_lower in record_lower:
                return record_lower[key_lower]
        
        for original_key in record.keys():
            clean_original = re.sub(r'[^a-z0-9]', '', str(original_key).lower())
            for key in possible_keys:
                clean_key = re.sub(r'[^a-z0-9]', '', key.lower())
                if clean_original == clean_key:
                    return original_key
        
        return None
    
    def _extract_field_value(self, record, field_aliases):
        """Extract field value from record using various aliases"""
        matching_key = self._find_matching_key(record, field_aliases)
        if matching_key and matching_key in record:
            value = record[matching_key]
            return str(value) if value is not None else ""
        return ""