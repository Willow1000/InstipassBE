# USER
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


# INSTITUTION
class InstitutionSignupToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)    
    
    def __str__(self):
        return f"{self.email}"

class InstitutionRegistrationToken(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    token = models.CharField(max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"
    

class Notifications(models.Model):
    message = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.channel} to {self.recepient_phone_number or self.recepient_email}" 

class ContactUsTracker(models.Model):
    fingerprint = models.CharField(max_length=64, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True) 

class DemoBookingTracker(models.Model):
    fingerprint = models.CharField(max_length=64, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

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
    template_front = models.ImageField(upload_to="institution_template")
    template_back = models.ImageField(upload_to="institution_template", null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution}"

class InstitutionToken(models.Model):
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE)
    token = models.CharField(max_length=512)
    lifetime = models.IntegerField()
    expiry_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

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


class Transaction(models.Model):
    CURRENCY_CHOICES = [
        ("KSH",'Kenyan Shillings'),
        ('USD',"US Dollars"),
        ("USDT","Tether")

    ]
    method = models.CharField(max_length = 20)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    gateway_response = models.JSONField(null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=5,choices=CURRENCY_CHOICES)
    processed_at = models.DateTimeField(auto_now_add=True)

    

class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("PENDING",'Pending'),
        ("SUCCESS",'Success'),
        ("REFUNDED",'Refunded')
    ]
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction,on_delete=models.CASCADE)
    status = models.CharField(max_length=10,choices=PAYMENT_STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.institution} {self.transaction}"

class NewsLetter(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add = True,null=True,blank=True)

    def __str__(self):
        return f"{self.email}"      

class ContactUs(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    message = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return f"{self.email}"         

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


# LOGS
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
    admin = models.ForeignKey(User,on_delete = models.CASCADE,null=True)
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
    action = models.CharField(max_length=30)
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

# STUDENTS
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



# models.py
class SubmissionTracker(models.Model):
    student = models.ForeignKey(Student,on_delete = models.CASCADE,null=True,blank=True)
    institution = models.ForeignKey(Institution,on_delete=models.CASCADE,blank=True,null=True)
    fingerprint = models.CharField(max_length=64, unique=True, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fingerprint} - {self.ip_address} - {self.institution}"

