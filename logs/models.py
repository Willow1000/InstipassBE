from django.db import models
import uuid
from accounts.models import User
from Id.models import *
from institution.models import DemoBooking,Payment

# IN PROD STOP USING UUID

class APIAccessLog(models.Model):
    REQUEST_METHOD_CHOICES = [
        ("GET",'GET'),
        ("POST","POST"),
        ('DELETE','DELETE'),
        ("PUT","PUT"),
        ("PATCH","PATCH")
    ]    

    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    endpoint = models.CharField(max_length=255)
    request_method = models.CharField(max_length=10,choices=REQUEST_METHOD_CHOICES)
    user_id = models.CharField(max_length=36)
    status_code = models.IntegerField(null=True,blank=True)
    ip_address = models.GenericIPAddressField(null=True,blank=True)
    request_timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} {self.endpoint} {self.ip_address} {self.status_code}"

    
class IdprogressLog(models.Model):
    Id = models.OneToOneField(IdOnQueue,on_delete=models.CASCADE)
    queued_on = models.DateTimeField(null=True,blank=True)
    started_processing = models.DateTimeField(null=True,blank=True)
    finished_processing = models.DateTimeField(null=True,blank=True)

    def __str__(self):
        return f"{self.Id}"

class AdminActionsLog(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    action = models.CharField(max_length=20)
    admin = models.ForeignKey(User,on_delete = models.CASCADE,null=True,blank=True)
    victim_type = models.CharField(max_length=40)
    victim = models.CharField(max_length=400)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.admin} {self.action} {self.victim}"

class BlackListLog(models.Model):
    REASON_CATEGORY_CHOICES = [
    ("invalid_docs", "Invalid or fake documentation"),
    ("payment_issue", "Payment not received"),
    ("fraud_suspected", "Fraud suspected"),
    ("policy_violation", "Violated platform policies"),
    ("inactivity", "Long-term inactivity"),
    ("manual_flag", "Flagged after manual review"),
    ("support_request", "Institution requested suspension"),
    ("other", "Other"),
]

    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    # action = models.CharField(max_length=30)
    admin = models.ForeignKey(User,on_delete = models.CASCADE,null=True,related_name="admin_blacklisting")
    victim = models.ForeignKey(User,on_delete = models.CASCADE,null=True,related_name="user_blacklisted")
    reason_category = models.CharField(max_length=20,choices=REASON_CATEGORY_CHOICES)
    reason_explanation = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin} {self.action} {self.victim}"

class DemoLogs(models.Model):
    admin = models.ForeignKey(User,on_delete=models.CASCADE)        
    demo = models.ForeignKey(DemoBooking,on_delete=models.CASCADE)
    action = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.demo}"


class ExportLog(models.Model):
    EXPORT_FORMAT_CHOICES = [
        ("csv", "CSV"),
        ("excel", "Excel"),
        ("json", "JSON"),
        ("pdf", "PDF"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="export_logs"
    )
    table_name = models.CharField(max_length=100)
    columns_exported = models.JSONField(null=True,blank=True)   # no need for json.dumps, JSONField handles it
    filters_applied = models.JSONField(null=True, blank=True)
    export_format = models.CharField(max_length=10, choices=EXPORT_FORMAT_CHOICES)
    record_count = models.PositiveIntegerField()
    file_size = models.BigIntegerField(help_text="Size of the exported file in bytes")
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Export Log"
        verbose_name_plural = "Export Logs"

    def __str__(self):
        return f"{self.user} exported {self.record_count} records from {self.table_name} ({self.export_format})"

class TransactionsLog(models.Model):
    admin = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    action = models.CharField(max_length=12)
    victim_type = models.CharField(max_length=24)
    victim = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin} {self.payment}"

    