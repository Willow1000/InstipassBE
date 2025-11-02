from rest_framework import serializers
from .models import *

class InstitutionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Institution
        fields = "__all__"

class InstitutionSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = InstitutionSettings
        fields = "__all__"        

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = "__all__"

class NewsLetterSerializer(serializers.ModelSerializer):
    class Meta:
        model=NewsLetter
        fields = "__all__"     

class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = "__all__"


class DemoBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DemoBooking
        exclude = ['status']      

class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue         
        fields = "__all__"    

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial     
        fields = "__all__"   

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Payment
        fields="__all__"        

class PaymentProofVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProofVerification
        fields = "__all__" 

class DeficitsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Deficits
        fields = "__all__"        
