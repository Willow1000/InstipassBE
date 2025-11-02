from rest_framework import serializers
from .models import User
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied 
from django.middleware.csrf import get_token


class UserSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    password1= serializers.CharField(write_only = True,min_length = 8)
    password = serializers.CharField(write_only =False ,min_length = 8)
    
    def validate(self,data):
        if data['password'] != data['password1']:
            raise serializers.ValidationError("Passwords do not match")
        if User.objects.filter(email=data['email']):
            raise serializers.ValidationError("User with email already exists")     
        return data    
        
    def create(self,validated_data):

        # role = self.context.get('role')
        role = 'institution'
        user=User.objects.create_user(username=validated_data["username"],email=validated_data['email'],password = validated_data['password1'],role=role)
     
        return user
        

class EmailTokenObtainPairSerializer(serializers.Serializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email')
        user = get_object_or_404(User, email=email)
        

        # Skip authenticate(), just issue tokens
        self.user = user
        return super().validate(attrs)

