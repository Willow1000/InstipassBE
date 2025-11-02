from django.contrib import admin
from .models import *
# Register your models here.

class StudentAdmin(admin.ModelAdmin):
    list_display = ('id','email','institution')
    list_filter = ('institution','email','id')
    search_field = ('institution','email')



admin.site.register(Student,StudentAdmin)


