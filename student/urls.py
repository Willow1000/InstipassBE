from django.urls import path,include
from rest_framework.routers import DefaultRouter
from .views import *
# from accounts.views import EmailTokenObtainPairView,CustomTokenRefreshView


router = DefaultRouter()
router.register('student',StudentViewSet,basename='studentApi')

urlpatterns = [
   
    # path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    # path('api/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path("api/",include(router.urls)),
  
]







