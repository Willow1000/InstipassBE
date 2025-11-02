from django.contrib import admin
from .models import User,InstitutionRegistrationToken,InstitutionSignupToken,BannedIP
# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ("id","email",'role')
    search_field = ("email",'role')
    list_filter = ("email","id")

class InstitutionSignupTokenAdmin(admin.ModelAdmin):
    list_filter = ['email']
    list_display = ["email"]
    search_field = ['email']

class InstitutionRegistrationTokenAdmin(admin.ModelAdmin):
    list_filter = ['user']
    list_display = ["user"]
    search_field = ['user']


@admin.register(BannedIP)
class BannedIPAdmin(admin.ModelAdmin):
    list_display = ("ip_address", "banned_until", "ban_count", "reason", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    search_fields = ("ip_address", "reason")
    list_filter = ("banned_until",)
    
admin.site.register(User,UserAdmin)   
admin.site.register(InstitutionSignupToken,InstitutionSignupTokenAdmin)
admin.site.register(InstitutionRegistrationToken,InstitutionRegistrationTokenAdmin) 