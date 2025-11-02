from django.db import models
from student.models import *

# Create your models here.
class IdOnQueue(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
class IdInProcess(models.Model):
    Id = models.OneToOneField(IdOnQueue,on_delete=models.CASCADE,primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pk}"
    
class IdReady(models.Model):
    Id = models.OneToOneField(IdInProcess,on_delete=models.CASCADE,primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.pk}"