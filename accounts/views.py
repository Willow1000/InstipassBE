from rest_framework import viewsets, status
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from .serializers import EmailTokenObtainPairSerializer
from .serializers import UserSerializer
from .models import User,SignupTracker,InstitutionSignupToken,BannedIP
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_protect
from institution.models import InstitutionMagicLinkToken,Institution,LoginTracker

from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.views import APIView
from institution.utils import decode_application_token
from rest_framework.response import Response
from InstiPass.tasks import send_email

from django.utils import timezone
import requests

from django.conf import settings


from institution.utils import generate_login_token

from dotenv import load_dotenv
import os

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from InstiPass.middleware import get_client_ip

from django.contrib.auth.views import PasswordContextMixin
from django.views.generic.edit import FormView
from accounts.forms import PasswordResetForm

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from django.http import Http404
from rest_framework_simplejwt.tokens import RefreshToken



# @csrf_exempt  # disable CSRF for this endpoint
@api_view(["POST"])
@permission_classes([AllowAny])  # allow unauthenticated access
def request_magic_link(request):
    email = request.data.get("email")
    fingerprint = request.data.get("fingerprint")
    cookie_flag = request.COOKIES.get("login_form_submitted")
    ip_address = get_client_ip(request)
    if (fingerprint and LoginTracker.objects.filter(fingerprint=fingerprint).count() >= 10) or LoginTracker.objects.filter(ip_address=ip_address).count() >= 10:
        response = Response({"detail": "Limit reached"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
                
                # Set cookie (valid for 1 year)
        expires = timezone.now() + timedelta(hours=2)
        response.set_cookie(
            key='login_form_submitted',
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
    if cookie_flag:
        return Response({"detail": "Limit Reached"}, status=status.HTTP_429_TOO_MANY_REQUESTS)
    if not email:
        return Response({"detail": "email required"}, status=status.HTTP_400_BAD_REQUEST)
   
    institution = get_object_or_404(Institution, email=email)

    # generate token + login link
    token_data = generate_login_token(email)
    token = token_data.get("token")
    expiry_date = token_data.get("expiry_date")
 
    InstitutionMagicLinkToken.objects.create(
        institution = institution,
        token=token,
        expiry_date = expiry_date
    )
    LoginTracker.objects.create(
        institution = institution,
        ip_address = ip_address,
        fingerprint = fingerprint,
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    return Response({"detail": "magic link sent"}, status=status.HTTP_200_OK)



class InstitutionViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.filter(role='institution')
    http_method_names = ['get','post','put','patch','delete']
   

    @method_decorator(ensure_csrf_cookie)
    def list(self, request):
        # Optionally list all students (or just forbid)
        return Response({"detail": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @method_decorator(ensure_csrf_cookie)
    def create(self, request):
        fingerprint = request.data.get('fingerprint')
        cookie_flag = request.COOKIES.get('form_submitted')

        # Block if fingerprint already submitted
        if fingerprint and SignupTracker.objects.filter(fingerprint=fingerprint).exists():
            return Response({"detail": "Already submitted with this device."}, status=status.HTTP_403_FORBIDDEN)

        # Block if no fingerprint but cookie exists
        if not fingerprint and cookie_flag:
            return Response({"detail": "Already submitted (cookie detected)."}, status=status.HTTP_403_FORBIDDEN)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():   
            serializer.save()

            # Log submission tracker
            SignupTracker.objects.create(
                fingerprint=fingerprint or None,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            response = Response({"detail": "registration successful."}, status=status.HTTP_201_CREATED)
            response.set_cookie('form_submitted', 'true', max_age=60 * 60 * 24 * 365, httponly=True)
            
            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)         




# from .models import InstitutionMagicLinkToken
from django.contrib.auth import get_user_model

User = get_user_model()


class MagicLinkTokenVerifierAPIView(APIView):
    """
    Takes a one-time magic link token, validates it,
    and issues fresh JWT access + refresh tokens.
    """
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        # Grab token from query or body
        token_str = request.query_params.get("token") or request.data.get("token")
        # print(token_str)

        if not token_str:
            return Response({"detail": "token is required"}, status=status.HTTP_400_BAD_REQUEST)
        # Validate against your magic link table
        token_obj = InstitutionMagicLinkToken.objects.filter(token=token_str).first()
        email = token_obj.institution.email
        user = get_object_or_404(User, email=email)
        if not user.is_active:
            # print("hapa")
            return Response({"detail": "user not active"}, status=status.HTTP_403_FORBIDDEN)
        if token_obj.expiry_date < timezone.now():
            # print("here")
            return Response({"detail": "token expired"}, status=status.HTTP_403_FORBIDDEN)
        if token_obj.used:
            # print("hapa 1")
            return Response({"detail": "token has been used"}, status=status.HTTP_403_FORBIDDEN)

        # Get user by email
        # email = token_obj.institution.email
        # user = get_object_or_404(User, email=email)


        # Mark token as used
       

        # Issue fresh JWTs
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        response = Response(
            {
                "access": access,
                "refresh": str(refresh),
            }
        )

        # Optional: set refresh cookie
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60 * 60 * 24,
        )
        token_obj.used = True
        token_obj.save()
        return response


class SignupTokenAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Step 1: Extract token from the JSON body
        
        token = request.data.get('token')
        if not token:
            return Response({'detail': 'Token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        token_obj=(InstitutionRegistrationToken.objects.filter(token=token).first() or InstitutionSignupToken.objects.filter(token=token).first())
        if token_obj:
            
            if token_obj.used:
                return Response({'detail': 'Token has been used.'}, status=status.HTTP_403_FORBIDDEN)
        
            # Step 2: Decode the token
            response = decode_application_token(token)

            # Step 3: Handle different cases
            if response == 'Token expired':
                return Response({'detail': 'Token has expired.'}, status=status.HTTP_401_UNAUTHORIZED)

            elif response == 'Token invalid':
                return Response({'detail': 'Token is invalid.'}, status=status.HTTP_401_UNAUTHORIZED)

            elif type(response) == 'dict':
                # Assume the decoded response contains institution_id or some valid payload
                institution_id = response.get('institution_id')
                token_obj.used = True
                token_obj.save()
                return Response({'institution_id': institution_id,'institution':institution}, status=status.HTTP_200_OK)   
            else:
                return Response({'detail': 'Token is invalid.'}, status=status.HTTP_400_BAD_REQUEST)   
        return Response({'detail': 'Token is does not exist'}, status=status.HTTP_400_BAD_REQUEST)



class CaptchaVerifyView(APIView):
    def post(self, request):
        ip = request.META.get("REMOTE_ADDR")
        token = request.data.get("token")

        if not token:
            return Response({"detail": "Missing token"}, status=400)

        # Verify with Google
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": os.getenv("RECAPTCHA_SECRET_KEY"),
            "response": token,
            "remoteip": ip,
        }
        r = requests.post(verify_url, data=data)
        result = r.json()

        if result.get("success"):
            request.session.pop("captcha_fails", None)
            return Response({"success": True})

        # Failed → increment counter
        fails = request.session.get("captcha_fails", 0) + 1
        request.session["captcha_fails"] = fails

        if fails >= settings.FAILED_CAPTCHA_LIMIT:
            banned, created = BannedIP.objects.get_or_create(
                ip_address=ip,
                defaults={
                    "banned_until": timezone.now() + timezone.timedelta(hours=1),
                    "ban_count": 1
                }
            )
            if not created:
                banned.extend_ban()

            return Response({
                "success": False,
                "banned": True,
                "permanent": banned.is_permanent,
            }, status=403)

        return Response({
            "success": False,
            "errors": result.get("error-codes", []),
            "fails": fails
        }, status=400)

  
