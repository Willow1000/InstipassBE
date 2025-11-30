from .models import *
from .serializers import *
import requests
import json
from institution.models import Institution
from rest_framework.parsers import MultiPartParser,JSONParser
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie



def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

# Create your views here.

class StudentViewSet(viewsets.ModelViewSet):
    # queryset = Student.objects.all().order_by('-created_at')
    parser_classes = (MultiPartParser,JSONParser)
    serializer_class = StudentSerializer
    
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    def get_queryset(self):
        return Student.objects.filter(email = self.request.user.email).order_by('-created_at')

    @method_decorator(ensure_csrf_cookie)
    def list(self, request):
        # Optionally list all students (or just forbid)
        return Response({"detail": "Method not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @method_decorator(ensure_csrf_cookie)
    def create(self, request):

        fingerprint = request.data.get('fingerprint')
        cookie_flag = request.COOKIES.get('form_submitted')
        
        token = request.GET.get('token')

        if token:
            # Block if fingerprint already submitted
       
            try:

                data = {
                "token":token
                        }

                response = requests.post("http://127.0.0.1:8000/institution/api/tokenvalidator",data=data)

                data = response.json()
           

                if fingerprint and SubmissionTracker.objects.filter(fingerprint=fingerprint).exists():
                    return Response({"detail": "Already submitted with this device."}, status=status.HTTP_403_FORBIDDEN)
                
                # if SubmissionTracker.objects.filter(user_agent=request.META.get('HTTP_USER_AGENT', '')).exists():
                #     return Response({"detail": "Already submitted with this device."}, status=status.HTTP_403_FORBIDDEN)
                # Block if no fingerprint but cookie exists
                if not fingerprint and cookie_flag:
                    return Response({"detail": "Already submitted (cookie detected)."}, status=status.HTTP_403_FORBIDDEN)
                raw_data = request.data

                clean_data = {
                    "institution": int(raw_data.get('institution')),
                    "reg_no": raw_data.get("reg_no"),
                    "first_name": raw_data.get("first_name"),
                    "last_name": raw_data.get("last_name"),
                    "course": raw_data.get("course"),
                    "admission_year": int(raw_data.get("admission_year")),
                    "email": raw_data.get("email"),
                    "phone_number": raw_data.get("phone_number"),
                    "fingerprint": raw_data.get("fingerprint"),
                    "photo": raw_data.get("photo"),  # keep InMemoryUploadedFile
                }

                institution = get_object_or_404(Institution,id=int(raw_data.get('institution')))
                # admission_year = request.data.get("admission_year")
                # data = dict(request.data)

                # data.update({"institution":[int(institution)],"admission_year":[int(admission_year)]})
                serializer = StudentSerializer(data=clean_data)
                # print(data)
                if serializer.is_valid():
                    student = serializer.save()  # capture the created Student instance
                    SubmissionTracker.objects.create(
                        student=student,  # 👈 link the student here
                        institution=institution,
                        fingerprint=fingerprint or None,
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )


                    response = Response({"detail": "Submission successful."}, status=status.HTTP_201_CREATED)
                    response.set_cookie('form_submitted', 'true', max_age=60 * 60 * 24 * 365, httponly=True)
                    return response
                elif serializer.errors:
                    print(serializer.errors)
                    return Response({"detail": "Error occurred try again later. If it persists contact support"}, status=status.HTTP_400_BAD_REQUEST)
                    # Log submission tracker
                   
            except Exception as e:
                print(f'An error occurred: {e}')
                return Response({"detail": "Error occurred try again later. If it persists contact support"}, status=status.HTTP_400_BAD_REQUEST)
        # serializer.save()


        else:
            return Response({"detail": "no token found"}, status=status.HTTP_400_BAD_REQUEST)    






