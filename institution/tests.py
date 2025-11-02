from django.test import TestCase
from rest_framework.test import APITestCase,APIClient
from rest_framework import status
from .models import *
from django.urls import reverse_lazy,reverse

# Create your tests here.
class TestInstitution(TestCase):
    def setUp(self):
        self.institution = Institution

    def test_create_institution(self):
        
        self.institution.objects.create(name="Uoe",county="Eldoret",region="Uasin Gishu",address="001100",email="uoe@gmail.com",tel="12345678")    
        self.assertEqual(self.institution.objects.first().name,"Uoe")

        self.assertEqual(self.institution.objects.all().count(),1)
    def test_get_institution(self):
        print(self.institution.objects.first())

class TestInstitutionApi(APITestCase):
    def setUp(self):
        self.data = data = {"name":"Uoe","county":"Eldoret","region":"Uasin Gishu","address":"001100","email":"uoe@gmail.com","tel":"12345678"}
        return super().setUp()
    def test_create_institution(self):  
        response = self.client.post(path = reverse_lazy("institutionApi-list"),data = self.data)
        self.assertEqual(response.status_code,status.HTTP_201_CREATED)
        self.assertEqual(Institution.objects.all().count(),1)
    def test_update_institution(self):
        self.client.post(path = reverse_lazy("institutionApi-list"),data = self.data)  
        respons = self.client.get(reverse("institutionApi-detail",kwargs ={"pk":2}))
        print("get res",respons,sep=":")
        print(reverse("institutionApi-detail",kwargs ={"pk":1}))
        response = self.client.patch(reverse("institutionApi-detail",kwargs ={"pk":1}),data={"county":"Marakwet"},format="json")
        print(response.status_code)
        # self.assertEqual(response.status_code,status.HTTP_200_OK)

