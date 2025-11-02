from django.db import models
from django.contrib.auth.models import AbstractUser,Group,Permission
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone
from django.conf import settings


# from institution.models import Institution
# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Creates and returns a regular user with the given email and password."""
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)  # Normalize email (lowercase)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # Hash password
        user.save(using=self._db)  # Save to database
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Creates and returns a superuser with all permissions."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
    

class User(AbstractUser):
    email = models.EmailField(unique=True)  
    # username = models.CharField(unique=False,max_length=50)# <--- This is the key line
    role = models.CharField(max_length=20)
    permissions = models.ManyToManyField(Permission, related_name="student_user_permissions")
    groups = models.ManyToManyField(Group, related_name="student_user_groups")
    
    objects = UserManager()
    # USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    def __str__(self):
        return self.username

class SignupTracker(models.Model):
    fingerprint = models.CharField(max_length=64, unique=True, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fingerprint} {self.ip_address}"



class InstitutionSignupToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=256)
    used = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)   
    updated_at = models.DateTimeField(auto_now=True) 
    
    def __str__(self):
        return f"{self.email}"

class InstitutionRegistrationToken(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    token = models.CharField(max_length=512)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return f"{self.user}"


class BannedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    banned_until = models.DateTimeField(null=True, blank=True)
    ban_count = models.PositiveIntegerField(default=1)
    reason = models.CharField(max_length=255, blank=True)  # optional
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-banned_until",)

    def is_active(self):
        return self.banned_until is not None and self.banned_until > timezone.now()

    def remaining_seconds(self):
        if not self.is_active():
            return 0
        return int((self.banned_until - timezone.now()).total_seconds())
    def extend_ban(self):
        """Increase count and duration progressively or permanently"""
        self.ban_count += 1

        if self.ban_count >= settings.IPBAN_PERMANENT_AFTER:
            # Permanent ban
            self.banned_until = None
        else:
            # Progressive ban duration (exponential: 1h, 2h, 4h…)
            extra_time = timedelta(hours=2 ** (self.ban_count - 1))
            self.banned_until = timezone.now() + extra_time

        self.save()

    @property
    def is_permanent(self):
        return self.banned_until is None

    def __str__(self):
        status = "active" if self.is_active() else "expired"
        return f"{self.ip_address} ({status}, count={self.ban_count})"

    
