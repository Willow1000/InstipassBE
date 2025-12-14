from django.db import models
from django.conf import settings


class AdminNotification(models.Model):
    URGENCY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    message = models.TextField(max_length=1000)  # longer than 250 chars
    url = models.URLField(max_length=500, blank=True, null=True)  # proper URL type
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default="low")

    # Optional: link to which admin/user gets the notification
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_notifications",
        null=True,
        blank=True,
    )

    # Track status
    # is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True,null=True)

    class Meta:
        ordering = ["-created_at"]  # Already has ordering (newest first)
        verbose_name = "Admin Notification"
        verbose_name_plural = "Admin Notifications"

    def __str__(self):
        return f"[{self.urgency.upper()}] {self.message[:50]}..."




 



class ContactUsTracker(models.Model):
    fingerprint = models.CharField(max_length=64, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['submitted_at']  # Order by submission date
        verbose_name = "Contact Us Tracker"
        verbose_name_plural = "Contact Us Trackers"

    def __str__(self):
        return f"Contact Us: {self.fingerprint} - {self.submitted_at}"


class DemoBookingTracker(models.Model):
    fingerprint = models.CharField(max_length=64, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['submitted_at']  # Order by submission date
        verbose_name = "Demo Booking Tracker"
        verbose_name_plural = "Demo Booking Trackers"

    def __str__(self):
        return f"Demo Booking: {self.fingerprint} - {self.submitted_at}"