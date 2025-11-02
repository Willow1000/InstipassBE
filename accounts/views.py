"""
Authentication and Institution Management API Views

This module contains views for handling institution authentication,
magic links, signup tokens, and security measures like CAPTCHA verification.
"""

from datetime import timedelta
import os
import requests

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordContextMixin
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from dotenv import load_dotenv
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.forms import PasswordResetForm
from institution.models import InstitutionMagicLinkToken, Institution, LoginTracker
from institution.utils import decode_application_token, generate_login_token
from InstiPass.middleware import get_client_ip
from InstiPass.tasks import send_email

from .models import User, SignupTracker, InstitutionSignupToken, BannedIP
from .serializers import EmailTokenObtainPairSerializer, UserSerializer

# Load environment variables
load_dotenv()

User = get_user_model()


@api_view(["POST"])
@permission_classes([AllowAny])
def request_magic_link(request):
    """
    Request a magic login link for institution authentication.
    
    This endpoint handles magic link requests with rate limiting based on
    fingerprint and IP address to prevent abuse.
    
    Args:
        request: HTTP request containing email and fingerprint
        
    Returns:
        Response: Success message or error with appropriate status code
    """
    email = request.data.get("email")
    fingerprint = request.data.get("fingerprint")
    cookie_flag = request.COOKIES.get("login_form_submitted")
    ip_address = get_client_ip(request)
    
    # Rate limiting check
    if (fingerprint and LoginTracker.objects.filter(fingerprint=fingerprint).count() >= 10) or \
       LoginTracker.objects.filter(ip_address=ip_address).count() >= 10:
        
        response = Response(
            {"detail": "Limit reached"}, 
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
        
        # Set cookie (valid for 1 year)
        expires = timezone.now() + timedelta(hours=2)
        response.set_cookie(
            key='login_form_submitted',
            value='true',
            expires=expires,
            secure=True,  # Only over HTTPS
            samesite='Lax',
            path='/'
        )
        
        # Ban IP address for excessive requests
        banned_ip = BannedIP.objects.filter(ip_address=ip_address).last()
        if banned_ip:
            banned_ip.extend_ban()
        else:
            BannedIP.objects.create(
                ip_address=ip_address,
                banned_until=timezone.now() + timedelta(days=365),
                reason="Exceeded demo booking limit"
            )
        return response
    
    # Check if cookie flag exists (already submitted)
    if cookie_flag:
        return Response(
            {"detail": "Limit Reached"}, 
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    # Validate email
    if not email:
        return Response(
            {"detail": "email required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get institution and generate magic link
    institution = get_object_or_404(Institution, email=email)
    token_data = generate_login_token(email)
    token = token_data.get("token")
    expiry_date = token_data.get("expiry_date")
    
    # Create magic link token
    InstitutionMagicLinkToken.objects.create(
        institution=institution,
        token=token,
        expiry_date=expiry_date
    )
    
    # Log login attempt
    LoginTracker.objects.create(
        institution=institution,
        ip_address=ip_address,
        fingerprint=fingerprint,
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response(
        {"detail": "magic link sent"}, 
        status=status.HTTP_200_OK
    )


class InstitutionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Institution users.
    
    Provides CRUD operations for Institution users with additional
    security measures for user registration.
    """
    
    serializer_class = UserSerializer
    queryset = User.objects.filter(role='institution')
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    @method_decorator(ensure_csrf_cookie)
    def list(self, request):
        """
        List institution users (currently disabled for security).
        
        Returns:
            Response: Method not allowed error
        """
        return Response(
            {"detail": "Method not allowed."}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @method_decorator(ensure_csrf_cookie)
    def create(self, request):
        """
        Create a new institution user with anti-spam measures.
        
        Uses fingerprint and cookies to prevent duplicate submissions
        and abuse.
        
        Args:
            request: HTTP request containing user data and fingerprint
            
        Returns:
            Response: Registration success or error message
        """
        fingerprint = request.data.get('fingerprint')
        cookie_flag = request.COOKIES.get('form_submitted')

        # Anti-spam checks
        if fingerprint and SignupTracker.objects.filter(fingerprint=fingerprint).exists():
            return Response(
                {"detail": "Already submitted with this device."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        if not fingerprint and cookie_flag:
            return Response(
                {"detail": "Already submitted (cookie detected)."}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and save user
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():   
            serializer.save()

            # Log submission for anti-spam tracking
            SignupTracker.objects.create(
                fingerprint=fingerprint or None,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )

            response = Response(
                {"detail": "registration successful."}, 
                status=status.HTTP_201_CREATED
            )
            # Set cookie to prevent duplicate submissions
            response.set_cookie(
                'form_submitted', 
                'true', 
                max_age=60 * 60 * 24 * 365, 
                httponly=True
            )
            
            return response

        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


class MagicLinkTokenVerifierAPIView(APIView):
    """
    API View for verifying magic link tokens and issuing JWT tokens.
    
    Validates one-time magic link tokens and exchanges them for
    JWT access and refresh tokens for authenticated sessions.
    """
    
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        Verify magic link token and issue JWT tokens.
        
        Args:
            request: HTTP request containing magic link token
            
        Returns:
            Response: JWT tokens or validation error
        """
        # Extract token from query parameters or request body
        token_str = request.query_params.get("token") or request.data.get("token")
        
        if not token_str:
            return Response(
                {"detail": "token is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate magic link token
        token_obj = InstitutionMagicLinkToken.objects.filter(token=token_str).first()
        if not token_obj:
            return Response(
                {"detail": "Invalid token"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        email = token_obj.institution.email
        user = get_object_or_404(User, email=email)
        
        # Check user status and token validity
        if not user.is_active:
            return Response(
                {"detail": "user not active"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if token_obj.expiry_date < timezone.now():
            return Response(
                {"detail": "token expired"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if token_obj.used:
            return Response(
                {"detail": "token has been used"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        # Prepare response with tokens
        response = Response(
            {
                "access": access,
                "refresh": str(refresh),
            }
        )

        # Set refresh token as HTTP-only cookie
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=60 * 60 * 24,
        )
        
        # Mark token as used
        token_obj.used = True
        token_obj.save()
        
        return response


class SignupTokenAPIView(APIView):
    """
    API View for validating institution signup tokens.
    
    Handles the verification of signup tokens during the institution
    registration process.
    """
    
    def post(self, request, *args, **kwargs):
        """
        Validate institution signup token.
        
        Args:
            request: HTTP request containing token
            
        Returns:
            Response: Token validation result or error
        """
        token = request.data.get('token')
        if not token:
            return Response(
                {'detail': 'Token is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Look for token in both token tables
        token_obj = (InstitutionRegistrationToken.objects.filter(token=token).first() or 
                    InstitutionSignupToken.objects.filter(token=token).first())
        
        if not token_obj:
            return Response(
                {'detail': 'Token does not exist'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if token_obj.used:
            return Response(
                {'detail': 'Token has been used.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Decode and validate token
        response = decode_application_token(token)

        # Handle different validation outcomes
        if response == 'Token expired':
            return Response(
                {'detail': 'Token has expired.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        elif response == 'Token invalid':
            return Response(
                {'detail': 'Token is invalid.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        elif isinstance(response, dict):
            # Valid token - return institution data
            institution_id = response.get('institution_id')
            token_obj.used = True
            token_obj.save()
            return Response(
                {'institution_id': institution_id, 'institution': institution}, 
                status=status.HTTP_200_OK
            )   
        else:
            return Response(
                {'detail': 'Token is invalid.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class CaptchaVerifyView(APIView):
    """
    API View for CAPTCHA verification with rate limiting.
    
    Handles reCAPTCHA verification and implements security measures
    to prevent brute force attacks.
    """
    
    def post(self, request):
        """
        Verify CAPTCHA token and apply security measures.
        
        Args:
            request: HTTP request containing CAPTCHA token
            
        Returns:
            Response: CAPTCHA verification result
        """
        ip = request.META.get("REMOTE_ADDR")
        token = request.data.get("token")

        if not token:
            return Response(
                {"detail": "Missing token"}, 
                status=400
            )

        # Verify CAPTCHA with Google
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        data = {
            "secret": os.getenv("RECAPTCHA_SECRET_KEY"),
            "response": token,
            "remoteip": ip,
        }
        
        r = requests.post(verify_url, data=data)
        result = r.json()

        if result.get("success"):
            # Successful verification - reset failure counter
            request.session.pop("captcha_fails", None)
            return Response({"success": True})

        # Failed verification - increment counter
        fails = request.session.get("captcha_fails", 0) + 1
        request.session["captcha_fails"] = fails

        # Check if user should be banned
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