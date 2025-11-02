"""
Django Models for Institution Management System

This module defines all data models for institutions, payments, demos, 
and related functionality in the InstiPass system.
"""

from django.core.validators import (FileExtensionValidator, MaxValueValidator,
                                    MinValueValidator)
from django.db import models
from django.utils.timezone import now

from accounts.models import User


class Institution(models.Model):
    """
    Represents an educational institution in the system.
    
    Stores comprehensive information about universities, colleges, polytechnics,
    and institutes including location, contact details, and administrative information.
    """
    
    # Region choices for Kenyan institutions
    REGION_CHOICES = [
        ("Central", "Central"),
        ("Coast", "Coast"),
        ("Eastern", "Eastern"),
        ("Nairobi", "Nairobi"),
        ("North Eastern", "North Eastern"),
        ("Nyanza", "Nyanza"),
        ("Rift Valley", "Rift Valley"),
        ("Western", "Western"),
    ]

    # County choices for Kenyan institutions
    COUNTY_CHOICES = [
        ("Mombasa", "Mombasa"),
        ("Kwale", "Kwale"),
        ("Kilifi", "Kilifi"),
        ("Tana River", "Tana River"),
        ("Lamu", "Lamu"),
        ("Taita Taveta", "Taita Taveta"),
        ("Garissa", "Garissa"),
        ("Wajir", "Wajir"),
        ("Mandera", "Mandera"),
        ("Marsabit", "Marsabit"),
        ("Isiolo", "Isiolo"),
        ("Meru", "Meru"),
        ("Tharaka-Nithi", "Tharaka-Nithi"),
        ("Embu", "Embu"),
        ("Kitui", "Kitui"),
        ("Machakos", "Machakos"),
        ("Makueni", "Makueni"),
        ("Nyandarua", "Nyandarua"),
        ("Nyeri", "Nyeri"),
        ("Kirinyaga", "Kirinyaga"),
        ("Murang'a", "Murang'a"),
        ("Kiambu", "Kiambu"),
        ("Turkana", "Turkana"),
        ("West Pokot", "West Pokot"),
        ("Samburu", "Samburu"),
        ("Trans Nzoia", "Trans Nzoia"),
        ("Uasin Gishu (Eldoret)", "Uasin Gishu (Eldoret)"),
        ("Elgeyo Marakwet", "Elgeyo Marakwet"),
        ("Nandi", "Nandi"),
        ("Baringo", "Baringo"),
        ("Laikipia", "Laikipia"),
        ("Nakuru", "Nakuru"),
        ("Narok", "Narok"),
        ("Kajiado", "Kajiado"),
        ("Kericho", "Kericho"),
        ("Bomet", "Bomet"),
        ("Kakamega", "Kakamega"),
        ("Vihiga", "Vihiga"),
        ("Bungoma", "Bungoma"),
        ("Busia", "Busia"),
        ("Siaya", "Siaya"),
        ("Kisumu", "Kisumu"),
        ("Homa Bay", "Homa Bay"),
        ("Migori", "Migori"),
        ("Kisii", "Kisii"),
        ("Nyamira", "Nyamira"),
        ("Nairobi", "Nairobi"),
    ]

    # Institution type classifications
    INSTITUTION_TYPES = [
        ("University", "university"),
        ("College", "college"),
        ("Polytechnic", "polytechnic"),
        ("Institute", "institute")
    ]

    # Basic institution information
    name = models.CharField(max_length=100, help_text="Official name of the institution")
    region = models.CharField(max_length=100, choices=REGION_CHOICES, help_text="Geographical region in Kenya")
    county = models.CharField(max_length=100, choices=COUNTY_CHOICES, help_text="County location in Kenya")
    address = models.CharField(max_length=100, help_text="Physical address of the institution")
    email = models.EmailField(help_text="Primary institutional email address")
    institution_type = models.CharField(
        max_length=20, 
        choices=INSTITUTION_TYPES, 
        default='',
        help_text="Type of educational institution"
    )
    
    # Contact and web presence
    web_url = models.URLField(max_length=100, blank=True, null=True, help_text="Institution website URL")
    admin_email = models.EmailField(max_length=100, unique=True, help_text="Administrator email address")
    admin_tell = models.CharField(max_length=70, unique=True, help_text="Administrator telephone number")
    tel = models.CharField(max_length=70, help_text="Institution main telephone number")
    
    # Media and branding
    logo = models.ImageField(upload_to="institution_logo", default='', help_text="Institution logo image")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text="Record creation timestamp")
    updated_at = models.DateTimeField(auto_now=True, help_text="Record last update timestamp")

    def __str__(self):
        return f"{self.name}"

    class Meta:
        verbose_name = "Institution"
        verbose_name_plural = "Institutions"
        ordering = ['name']


class InstitutionSettings(models.Model):
    """
    Configuration and settings for each institution.
    
    Stores institution-specific preferences, notification settings, 
    template configurations, and operational parameters.
    """
    
    # Notification preference choices
    NOTIFICATION_CHOICES = [
        ("email", "Email"),
        ("sms", "SMS"),
        ("both", "Both")
    ]
    
    # ID generation settings
    qrcode = models.BooleanField(help_text="Enable QR code generation for student IDs")
    barcode = models.BooleanField(default=True, help_text="Enable barcode generation for student IDs")
    
    # Operational settings
    expected_total = models.IntegerField(help_text="Expected total number of students")
    institution = models.OneToOneField(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Related institution for these settings"
    )
    min_admission_year = models.IntegerField(
        validators=[MinValueValidator(2020), MaxValueValidator(now().year)],
        help_text="Minimum allowed admission year"
    )
    notification_pref = models.CharField(
        choices=NOTIFICATION_CHOICES, 
        max_length=100,
        help_text="Preferred notification method"
    )
    
    # Template and design settings
    template_front = models.ImageField(
        upload_to="institution_template", 
        null=True, 
        blank=True,
        help_text="Front template for student IDs"
    )
    template_back = models.ImageField(
        upload_to="institution_template", 
        null=True, 
        blank=True,
        help_text="Back template for student IDs"
    )
    
    # Data configuration
    courses_offered = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of courses offered by the institution"
    )
    conf_data = models.FileField(
        upload_to="conf_data/",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx", "csv", "json"])],
        null=True,
        blank=True,
        unique=True,
        help_text="Configuration data file for institution setup"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.institution}"

    class Meta:
        verbose_name = "Institution Settings"
        verbose_name_plural = "Institution Settings"


class StudentRegistrationToken(models.Model):
    """
    Tokens for student registration processes.
    
    Generates and tracks tokens used for bulk student registration
    with expiration and institutional association.
    """
    
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Institution this token belongs to"
    )
    token = models.CharField(max_length=512, help_text="Registration token string")
    lifetime = models.IntegerField(help_text="Token lifetime in hours")
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="Token expiration datetime")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Registration token for {self.institution}'

    class Meta:
        verbose_name = "Student Registration Token"
        verbose_name_plural = "Student Registration Tokens"


class RegistrationTracker(models.Model):
    """
    Tracks institution registration attempts for security and analytics.
    
    Records fingerprint, IP address, and user agent information
    to prevent spam and track registration patterns.
    """
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        help_text="User who completed registration (if applicable)"
    )
    fingerprint = models.CharField(
        max_length=64, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Browser fingerprint for duplicate detection"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of registrant")
    user_agent = models.TextField(blank=True, null=True, help_text="Browser user agent string")
    submitted_at = models.DateTimeField(auto_now_add=True, help_text="Registration attempt timestamp")

    def __str__(self):
        return f"Registration attempt from {self.fingerprint} at {self.submitted_at}"

    class Meta:
        verbose_name = "Registration Tracker"
        verbose_name_plural = "Registration Trackers"
        ordering = ['-submitted_at']


class Notifications(models.Model):
    """
    System notifications for institutions.
    
    Stores and manages various types of notifications sent to institutions
    including success, warning, error, and informational messages.
    """
    
    NOTIFICATION_TYPE_CHOICES = [
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('info', 'Info'),
    ]
    
    title = models.CharField(max_length=30, null=True, blank=True, help_text="Notification title")
    recipient = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Institution receiving the notification"
    )
    type = models.CharField(
        max_length=10, 
        choices=NOTIFICATION_TYPE_CHOICES, 
        null=True, 
        blank=True,
        help_text="Type of notification"
    )
    message = models.CharField(max_length=250, help_text="Notification message content")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Notification creation timestamp")

    def __str__(self):
        return f"{self.type.title()} notification to {self.recipient.email}"

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']


class PaymentProofVerification(models.Model):
    """
    Manages payment proof submission and verification process.
    
    Tracks payment documents submitted by institutions and their
    verification status by administrators.
    """
    
    STATUS_CHOICES = [
        ("UNDER REVIEW", "Under Review"),
        ("APPROVED", 'Approved'),
        ("REJECTED", 'Rejected')
    ]
    
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Institution that submitted the payment proof"
    )
    document = models.FileField(
        upload_to="payment_proofs",
        help_text="Uploaded payment proof document"
    )
    admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Admin who reviewed the payment proof"
    )
    status = models.CharField(
        choices=STATUS_CHOICES, 
        max_length=15, 
        default="UNDER REVIEW",
        help_text="Current verification status"
    )
    remarks = models.CharField(
        max_length=150, 
        null=True, 
        blank=True,
        help_text="Admin remarks or comments"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment proof for {self.institution} - {self.status}"

    class Meta:
        verbose_name = "Payment Proof Verification"
        verbose_name_plural = "Payment Proof Verifications"
        ordering = ['-created_at']


class Payment(models.Model):
    """
    Records financial transactions and payments made by institutions.
    
    Tracks payment methods, amounts, currencies, and associated
    verification documents for institutional payments.
    """
    
    CURRENCY_CHOICES = [
        ("KSH", 'Kenyan Shillings'),
        ('USD', "US Dollars"),
        ("USDT", "Tether")
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ("MPESA", "Mpesa"),
        ("BANK", "Bank"),
        ("CASH", "Cash"),
        ("CRYPTO", "Crypto")
    ]
    
    method = models.CharField(max_length=20, null=True, help_text="Payment method used")
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Payment amount"
    )
    gateway_response = models.JSONField(
        null=True, 
        blank=True,
        help_text="Raw response from payment gateway"
    )
    proof = models.ForeignKey(
        PaymentProofVerification, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Associated payment proof verification"
    )
    reference_number = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Payment reference number"
    )
    currency = models.CharField(
        max_length=5, 
        choices=CURRENCY_CHOICES, 
        null=True,
        help_text="Payment currency"
    )
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Institution that made the payment"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment #{self.reference_number} - {self.institution}"

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']


class PaymentReceiptDownloadToken(models.Model):
    """
    Secure tokens for downloading payment receipts.
    
    Generates time-limited tokens that allow secure download
    of payment receipts with usage tracking.
    """
    
    payment = models.ForeignKey(
        Payment, 
        on_delete=models.CASCADE,
        help_text="Payment associated with this receipt"
    )
    token = models.CharField(max_length=512, help_text="Download token string")
    used = models.BooleanField(default=False, help_text="Whether token has been used")
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="Token expiration datetime")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Receipt token for {self.payment}"

    class Meta:
        verbose_name = "Payment Receipt Download Token"
        verbose_name_plural = "Payment Receipt Download Tokens"


class InvoiceDownloadToken(models.Model):
    """
    Secure tokens for downloading invoices.
    
    Generates time-limited tokens that allow secure download
    of invoices with usage tracking and email association.
    """
    
    email = models.EmailField(help_text="Email address associated with the invoice")
    token = models.CharField(max_length=512, help_text="Download token string")
    used = models.BooleanField(default=False, help_text="Whether token has been used")
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="Token expiration datetime")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice token for {self.email}"

    class Meta:
        verbose_name = "Invoice Download Token"
        verbose_name_plural = "Invoice Download Tokens"


class Deficits(models.Model):
    """
    Tracks financial deficits or outstanding balances for institutions.
    
    Records different types of payment deficits including down payments,
    final payments, and adjustments for institutional accounts.
    """
    
    BALANCE_TYPE_CHOICES = [
        ("DOWNPAYMENT", "Down Payment"),
        ("FINAL_PAYMENT", "Final Payment"),
        ("ADJUSTMENT", "Adjustment / Correction"),
        ("", 'Not Specified')
    ]

    institution = models.OneToOneField(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Institution with the deficit"
    )
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Deficit amount"
    )
    type = models.CharField(
        max_length=13, 
        choices=BALANCE_TYPE_CHOICES, 
        null=True, 
        default='',
        help_text="Type of deficit"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deficit for {self.institution}: {self.amount}"

    class Meta:
        verbose_name = "Deficit"
        verbose_name_plural = "Deficits"


class NewsLetter(models.Model):
    """
    Stores newsletter subscription emails.
    
    Tracks email addresses that have subscribed to system
    newsletters and updates.
    """
    
    email = models.EmailField(unique=True, help_text="Subscriber email address")
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Newsletter subscriber: {self.email}"

    class Meta:
        verbose_name = "Newsletter Subscription"
        verbose_name_plural = "Newsletter Subscriptions"
        ordering = ['-created_at']


class ContactUs(models.Model):
    """
    Stores contact form submissions from users.
    
    Records messages, names, and contact information from
    users reaching out through the contact form.
    """
    
    name = models.CharField(max_length=50, help_text="Contact person's name")
    email = models.EmailField(help_text="Contact email address")
    message = models.CharField(max_length=300, help_text="Contact message content")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"Contact from {self.email}"

    class Meta:
        verbose_name = "Contact Us Message"
        verbose_name_plural = "Contact Us Messages"
        ordering = ['-created_at']


class DemoBooking(models.Model):
    """
    Manages demo session bookings for potential clients.
    
    Tracks demo requests, scheduling information, institution details,
    and booking status throughout the demo process.
    """
    
    # Status choices for tracking the demo booking
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Institution size categories
    SIZE_CHOICES = [
        ('S', '50-200 students'),
        ('M', '201-1,000 students'),
        ('L', '1,001-4,000 students'),
        ('XL', '4,001-6,000 students'),
        ('XXL', '6001+ students'),
    ]
    
    # Personal information
    name = models.CharField(
        max_length=255, 
        help_text="Full name of the person booking the demo"
    )
    email = models.EmailField(help_text="Email address for communication")
    phone_number = models.CharField(
        max_length=20, 
        help_text="Contact phone number"
    )
    
    # Institution information
    institution = models.CharField(
        max_length=255, 
        help_text="Name of the institution"
    )
    size = models.CharField(
        max_length=70, 
        choices=SIZE_CHOICES,
        help_text="Size category of the institution"
    )
    
    # Scheduling information
    date = models.DateField(help_text="Preferred date for the demo")
    time = models.CharField(max_length=25, help_text="Preferred time for the demo")
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED',
        help_text="Current status of the demo booking",
        null=True,
        blank=True
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True, 
        help_text="When the booking was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        help_text="When the booking was last updated"
    )
    
    def __str__(self):
        return f"{self.name} - {self.institution} ({self.date})"
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Demo Booking"
        verbose_name_plural = "Demo Bookings"


class Issue(models.Model):
    """
    Tracks support issues and helpdesk tickets.
    
    Manages institutional issues, bug reports, and support requests
    with assignment, status tracking, and resolution management.
    """
    
    ISSUE_TYPES = [
        ("bug", "Bug/Technical Error"),
        ("payment", "Payment Issue"),
        ("template", "ID Template Issue"),
        ("fraud", "Fraud/Suspicious Activity"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("rejected", "Rejected"),
    ]

    institution = models.ForeignKey(
        "Institution", 
        on_delete=models.CASCADE, 
        related_name="issues",
        help_text="Institution reporting the issue"
    )
    issue_type = models.CharField(
        max_length=20, 
        choices=ISSUE_TYPES, 
        default="other",
        help_text="Type of issue being reported"
    )
    description = models.TextField(help_text="Detailed description of the issue")
    attachment = models.FileField(
        upload_to="issue_attachments/", 
        null=True, 
        blank=True,
        help_text="Optional file attachment for the issue"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default="open",
        help_text="Current status of the issue"
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="assigned_issues",
        help_text="Admin user assigned to resolve this issue"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True, help_text="When issue was resolved")

    def __str__(self):
        return f"{self.institution.name} - {self.issue_type} ({self.status})"

    class Meta:
        verbose_name = "Issue"
        verbose_name_plural = "Issues"
        ordering = ['-created_at']


class Testimonial(models.Model):
    """
    Stores institutional testimonials and reviews.
    
    Records feedback, ratings, and quotes from institutions
    about their experience with the system.
    """
    
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Institution providing the testimonial"
    )
    author = models.CharField(max_length=20, help_text="Name of the testimonial author")
    quote = models.TextField(help_text="Testimonial content")
    rating = models.FloatField(help_text="Rating score (e.g., 4.5 out of 5)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial from {self.institution}"

    class Meta:
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"
        ordering = ['-created_at']


class InstitutionMagicLinkToken(models.Model):
    """
    Magic link tokens for secure institution authentication.
    
    Generates and manages one-time use tokens for passwordless
    login access for institutional administrators.
    """
    
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE,
        help_text="Institution this magic link is for"
    )
    token = models.CharField(max_length=512, help_text="Magic link token string")
    used = models.BooleanField(default=False, help_text="Whether token has been used")
    expiry_date = models.DateTimeField(null=True, blank=True, help_text="Token expiration datetime")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Magic link token for {self.institution}"

    class Meta:
        verbose_name = "Institution Magic Link Token"
        verbose_name_plural = "Institution Magic Link Tokens"


class LoginTracker(models.Model):
    """
    Tracks institution login attempts for security monitoring.
    
    Records login attempts with fingerprint, IP address, and
    user agent information for security and analytics.
    """
    
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Institution attempting login"
    )
    fingerprint = models.CharField(
        max_length=64, 
        blank=True, 
        null=True,
        help_text="Browser fingerprint for login attempt"
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address used for login attempt"
    )
    user_agent = models.TextField(
        blank=True, 
        null=True,
        help_text="Browser user agent string"
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Login attempt timestamp"
    )

    def __str__(self):
        return f"Login attempt from {self.ip_address} at {self.submitted_at}"

    class Meta:
        verbose_name = "Login Tracker"
        verbose_name_plural = "Login Trackers"
        ordering = ['-submitted_at']