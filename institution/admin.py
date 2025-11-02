from django.contrib import admin
from .models import *
from accounts.models import InstitutionRegistrationToken
# Register your models here.

class InstitutionAdmin(admin.ModelAdmin):
    list_filter = ("email",'id')
    list_display = ("email",'name')
    search_field = ("name","email","region")    

class InstitutionSettingsAdmin(admin.ModelAdmin):
    list_filter = ("institution",'id')
    list_display = ("institution",'id')
    search_field = ("institution") 

class NotificationsAdmin(admin.ModelAdmin):
    list_filter = ("recipient",'created_at')
    list_display = ("recipient",'created_at')
    search_field = ("recipient",'created_at')


# Register your models here.
class NewsLetterAdmin(admin.ModelAdmin):
    list_filter = ["email"]
    list_display = ["email"]
    search_field = ["email"]

class StudentRegistrationTokenAdmin(admin.ModelAdmin):
    list_filter = ['expiry_date']
    list_display = ["institution"]
    search_field = ['institution']

class InstitutionMagicLinkTokenAdmin(admin.ModelAdmin):
    list_filter = ["institution","created_at"]
    list_display = ["institution","created_at"]
    search_field = ["institution","created_at"]

class PaymentAdmin(admin.ModelAdmin):
    list_filter = ["institution","created_at"]
    list_display = ["institution","created_at"]
    search_field = ["institution","created_at"]

class PaymentProofVerificationAdmin(admin.ModelAdmin):
    list_filter = ["institution","created_at"]
    list_display = ["institution","created_at"]
    search_field = ["institution","created_at"]    

class DeficitsAdmin(admin.ModelAdmin):
    list_filter = ["institution","created_at"]
    list_display = ["institution","created_at"]
    search_field = ["institution","created_at"]        

admin.site.register(NewsLetter,NewsLetterAdmin)
admin.site.register(InstitutionMagicLinkToken,InstitutionMagicLinkTokenAdmin)
admin.site.register(Payment,PaymentAdmin)
admin.site.register(Deficits,DeficitsAdmin)
admin.site.register(PaymentProofVerification,PaymentProofVerificationAdmin)
admin.site.register(Institution,InstitutionAdmin)
admin.site.register(StudentRegistrationToken,StudentRegistrationTokenAdmin)
admin.site.register(InstitutionSettings,InstitutionSettingsAdmin)
admin.site.register(Notifications,NotificationsAdmin)