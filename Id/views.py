from django.shortcuts import render
from django.views.generic import CreateView,TemplateView
from .models import *
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# Create your views here.

class CreateIdInProcess(LoginRequiredMixin,UserPassesTestMixin,CreateView):
    template_name = 'id_process.html'
    model = IdInProcess
    login_url = reverse_lazy('adminLogin')
    redirect_field_name = "next"
    success_url = reverse_lazy("superuser_home")
    fields = [
        "Id"
    ]
    
    redirect_field_name = "next"
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class CreateIdReady(LoginRequiredMixin,UserPassesTestMixin,CreateView):
    template_name = 'id_ready.html'
    model = IdReady
    login_url = reverse_lazy('adminLogin')
    redirect_field_name = "next"
    success_url = reverse_lazy("superuser_home")
    fields = [
        "Id"
    ]    
    
    redirect_field_name = "next"
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class HomeView(TemplateView):
    template_name = 'superuser_home.html'