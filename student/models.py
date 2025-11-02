from django.db import models
from institution.models import Institution
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator,MaxValueValidator
from django.utils import timezone
# Create your models here.
class Student(models.Model):
    STATUS_CHOICES = (
        ('application_received', "Application has been received"),
        ("id_processing", "Your ID is being Processed"),
        ("id_ready", "Your ID is ready")
    )

    institution = models.ForeignKey(
        Institution , on_delete=models.CASCADE, related_name='student_institution'
    )
    reg_no = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    admission_year = models.IntegerField(
        validators=[
            MinValueValidator(2020), 
            MaxValueValidator(2025)
        ]
    )
    email = models.EmailField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=100, unique=True)
    photo = models.ImageField(upload_to='student_photo')
    status = models.CharField(
        choices=STATUS_CHOICES, max_length=100, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['institution', 'reg_no'],
                name='unique_institution_reg_no'
            )
        ]

    def __str__(self):
        return f"{self.institution}:{self.reg_no}"


class SubmissionTracker(models.Model):
    student = models.ForeignKey(Student,on_delete = models.CASCADE,null=True,blank=True)
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE,blank=True,null=True)
    fingerprint = models.CharField(max_length=64, unique=True, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fingerprint} - {self.ip_address} - {self.institution}"
