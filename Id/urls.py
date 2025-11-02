from django.urls import path
from .views import *

urlpatterns = [
    path('', HomeView.as_view(), name='superuser_home'),
    path('inprocess', CreateIdInProcess.as_view(), name='id_in_process'),
    path('ready/', CreateIdReady.as_view(), name='id_ready'),
]
