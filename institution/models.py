from django.db import models
from django.core.validators import MinValueValidator,MaxValueValidator
from accounts.models import User
from django.utils.timezone import now
from django.core.validators import FileExtensionValidator
# from accounts.models import User

# Create your models here.
class Institution(models.Model):
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

    INSTITUTION_TYPES = [
        ("University","university"),
        ("College","college"),
        ("Polytechnic","polytechnic"),
        ("Institute","institute")
    ]

    name = models.CharField(max_length=100)
    region = models.CharField(max_length=100,choices=REGION_CHOICES)
    county = models.CharField(max_length=100,choices=COUNTY_CHOICES)
    address = models.CharField(max_length=100)
    email = models.EmailField()
    institution_type = models.CharField(max_length=20,choices = INSTITUTION_TYPES,default = '')
    web_url = models.URLField(max_length=100,blank=True,null=True)
    admin_email=models.EmailField(max_length=100,unique=True)
    admin_tell = models.CharField(max_length=70,unique=True)
    logo = models.ImageField(upload_to="institution_logo",default='')
    tel = models.CharField(max_length=70)
    # admin = models.ForeignKey(User,on_delete=models.CASCADE,related_name="institution_admin",null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"
    

class InstitutionSettings(models.Model):
    NOTIFICATION_CHOICES = [
    ("email", "Email"),
    ("sms", "SMS"),
    ("both","Both")
]
    qrcode = models.BooleanField()
    barcode = models.BooleanField(default=True)
    expected_total = models.IntegerField()
    institution = models.OneToOneField(Institution,on_delete=models.CASCADE)  
    min_admission_year = models.IntegerField(validators=[MinValueValidator(2020),MaxValueValidator(now().year)])
    notification_pref = models.CharField(choices=NOTIFICATION_CHOICES,max_length=100)
    template_front = models.ImageField(upload_to="institution_template",null=True,blank=True)
    template_back = models.ImageField(upload_to="institution_template", null=True,blank=True)
    courses_offered = models.JSONField(default=list, blank=True)  # list of course names
    conf_data = models.FileField(
        upload_to="conf_data/",
        validators=[FileExtensionValidator(allowed_extensions=["xlsx", "csv","json"])],
        null=True,
        blank=True,
        unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution}"

class StudentRegistrationToken(models.Model):
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE)
    token = models.CharField(max_length=512)
    lifetime = models.IntegerField()
    # used = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.institution}'

class RegistrationTracker(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,blank=True,null=True)
    fingerprint = models.CharField(max_length=64, unique=True, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fingerprint} - {self.submitted_at}"

class Notifications(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
    ('success', 'Success'),
    ('warning', 'Warning'),
    ('error', 'Error'),
    ('info', 'Info'),
]
    
    title = models.CharField(max_length=30,null=True,blank=True)
    recipient = models.ForeignKey(Institution,on_delete = models.CASCADE)
    type = models.CharField(max_length=10,choices=NOTIFICATION_TYPE_CHOICES,null=True,blank=True)
    message = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message} to {self.recipient.email}" 


# class Transaction(models.Model):
class PaymentProofVerification(models.Model):
    STATUS_CHOICES=[
        ("UNDER REVIEW","Under Review"),
        ("APPROVED",'Approved'),
        ("REJECTED",'Rejected')
    ]
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE)
    document = models.FileField(upload_to="payment_proofs")
    admin = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    status = models.CharField(choices=STATUS_CHOICES,max_length=15,default="UNDER REVIEW")   
    remarks = models.CharField(max_length=150,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution} {self.updated_at}"


class Payment(models.Model):
    CURRENCY_CHOICES = [
        ("KSH",'Kenyan Shillings'),
        ('USD',"US Dollars"),
        ("USDT","Tether")

    ]
    PAYMENT_METHOD_CHOICES = [
        ("MPESA","Mpesa"),
        ("BANK","Bank"),
        ("CASH","Cash"),
        ("CRYPTO","Crypto")
    ]
    method = models.CharField(max_length = 20,null=True)
    amount=models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    gateway_response = models.JSONField(null=True,blank=True)
    proof = models.ForeignKey(PaymentProofVerification,on_delete=models.SET_NULL,null=True,blank=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=5,choices=CURRENCY_CHOICES,null=True)
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True,null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution} - {self.reference_number}"

class PaymentReceiptDownloadToken(models.Model):
    payment = models.ForeignKey(Payment,on_delete=models.CASCADE)
    token=models.CharField(max_length=512)
    used = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.payment}"

class InvoiceDownloadToken(models.Model):
    email = models.EmailField()
    token=models.CharField(max_length=512)
    used = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} {self.token}"

class Deficits(models.Model):
    BALANCE_TYPE_CHOICES = [
        ("DOWNPAYMENT", "Down Payment"),
        ("FINAL_PAYMENT", "Final Payment"),
        ("ADJUSTMENT", "Adjustment / Correction"),
        ("",'')
    ]

    institution = models.OneToOneField(Institution,on_delete=models.CASCADE)
    amount=models.DecimalField(max_digits=10, decimal_places=2,default=0.00)
    type = models.CharField(max_length=13,choices=BALANCE_TYPE_CHOICES,null=True,default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution}"

class NewsLetter(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add = True,null=True,blank=True)

    def __str__(self):
        return f"{self.email}"      

class ContactUs(models.Model):
    CATEGORY_CHOICES = [
        ("business", "Business Inquiry"),
        ("support", "Support"),
        ("bug", "Bug Report"),
        ("job", "Job Request"),
        ("spam", "Spam"),
        ("general", "General"),
    ]

    name = models.CharField(max_length=50)
    email = models.EmailField()
    message = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f"{self.email}"

    def save(self, *args, **kwargs):
        self.category = self._auto_categorize(self.message)
        super().save(*args, **kwargs)

    def _auto_categorize(self, msg: str):
        text = msg.lower()

        business_keywords = [
            "pricing", "quote", "institution", "integration", "api",
            "dashboard", "partnership", "bulk", "id system",'onboard','would like to use','how do i start'
        ]

        support_keywords = [
            "can't login", "cant login", "cannot login", "error", "issue",
            "problem", "help", "reset", "failed"
        ]

        spam_keywords = ["hi", "hello", "test", "hey", "asdf"]

        bug_keywords = ["404", "bug", "crash", "lag", "slow", "not loading","not working"]

        job_keywords = ["cv", "resume", "intern", "job", "hire", "opportunity","resourceful"]

        # Categorization logic
        if any(k in text for k in business_keywords):
            return "business"
        if any(k in text for k in support_keywords):
            return "support"
        if any(k in text for k in bug_keywords):
            return "bug"
        if any(k in text for k in job_keywords):
            return "job"
        if (any(k in text for k in spam_keywords)) and len(text) < 20:
            return "spam"

        return "general"
      

class DemoBooking(models.Model):
    # Status choices for tracking the demo booking
    STATUS_CHOICES = [
        ('SCHEDULED', 'scheduled'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    SIZE_CHOICES = [
        ('S', '50-200 students'),
        ('M', '201-1,000 students'),
        ('L', '1,001-4,000 students'),
        ('XL', '4,001-6,000 students'),
        ('XXL', '6001+ students'),
    ]
    # Personal information
    name = models.CharField(max_length=255, help_text="Full name of the person booking the demo")
    email = models.EmailField(help_text="Email address for communication")
    phone_number = models.CharField(max_length=20, help_text="Contact phone number")
    
    # Institution information
    institution = models.CharField(max_length=255, help_text="Name of the institution")
    size = models.CharField(max_length=70, help_text="Size of the institution" ,choices = SIZE_CHOICES)
    
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
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the booking was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the booking was last updated")
    
    def __str__(self):
        return f"{self.name} - {self.institution} ({self.date})"
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = "Demo Booking"
        verbose_name_plural = "Demo Bookings"              


class Issue(models.Model):
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
        "Institution", on_delete=models.CASCADE, related_name="issues"
    )

    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPES, default="other")
   
    description = models.TextField()
    attachment = models.FileField(upload_to="issue_attachments/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_issues"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.institution.name} - {self.issue_type} ({self.status})"

class Testimonial(models.Model):
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE)
    author = models.CharField(max_length=20)
    quote = models.TextField()
    rating = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.institution}"


class InstitutionMagicLinkToken(models.Model):
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE)
    token = models.CharField(max_length=512)
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField(null=True,blank=True)
    def __str__(self):
        return f"{self.institution}"        

class LoginTracker(models.Model):
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE,null=True,blank=True)
    fingerprint = models.CharField(max_length=64, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fingerprint} {self.ip_address}"
        