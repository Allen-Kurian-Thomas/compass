from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


class InternManager(BaseUserManager):
    def create_user(self, email, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('status', 'approved')
        return self.create_user(email, full_name, password, **extra_fields)


def generate_employee_id():
    last = Intern.objects.order_by('-employee_id').first()
    if last and last.employee_id:
        try:
            num = int(last.employee_id[2:]) + 1
        except (ValueError, TypeError):
            num = 1001
    else:
        num = 1001
    return f"TS{num}"


DEPARTMENT_CHOICES = [
    ('engineering', 'Engineering'),
    ('design', 'Design'),
    ('marketing', 'Marketing'),
    ('hr', 'Human Resources'),
    ('finance', 'Finance'),
    ('operations', 'Operations'),
    ('sales', 'Sales'),
    ('data_science', 'Data Science'),
    ('product', 'Product Management'),
    ('other', 'Other'),
]

GENDER_CHOICES = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Other'),
    ('prefer_not', 'Prefer not to say'),
]

BLOOD_GROUP_CHOICES = [
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'),
]

MARITAL_STATUS_CHOICES = [
    ('single', 'Single'),
    ('married', 'Married'),
    ('divorced', 'Divorced'),
    ('widowed', 'Widowed'),
]

STATUS_CHOICES = [
    ('pending', 'Pending Approval'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
]


class Intern(AbstractBaseUser, PermissionsMixin):
    # Core account fields
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    date_of_joining = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Django auth fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    profile_complete = models.BooleanField(default=False)

    # Personal
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    bio = models.TextField(blank=True)

    # Contact
    personal_phone = models.CharField(max_length=20, blank=True)
    skype_id = models.CharField(max_length=100, blank=True)
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)

    # Professional
    designation = models.CharField(max_length=100, blank=True)
    reporting_manager = models.CharField(max_length=150, blank=True)
    primary_unit = models.CharField(max_length=100, blank=True)
    total_experience = models.CharField(max_length=50, blank=True)

    # Financial
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)
    aadhaar_number = models.CharField(max_length=20, blank=True)

    # Statutory
    pf_uan = models.CharField(max_length=30, blank=True)
    pf_account_number = models.CharField(max_length=30, blank=True)
    passport_number = models.CharField(max_length=20, blank=True)

    # Family
    father_name = models.CharField(max_length=150, blank=True)
    mother_name = models.CharField(max_length=150, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)

    # Technical skills (stored as comma-separated tags)
    technical_skills = models.TextField(blank=True, help_text="Comma-separated skills e.g. Python, Django")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = InternManager()

    class Meta:
        verbose_name = 'Intern'
        verbose_name_plural = 'Interns'

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def get_skills_list(self):
        if self.technical_skills:
            return [s.strip() for s in self.technical_skills.split(',') if s.strip()]
        return []

    def save(self, *args, **kwargs):
        if not self.employee_id and self.status == 'approved':
            self.employee_id = generate_employee_id()
        super().save(*args, **kwargs)

    @property
    def first_name(self):
        return self.full_name.split()[0] if self.full_name else ''

    @property
    def last_name(self):
        parts = self.full_name.split()
        return ' '.join(parts[1:]) if len(parts) > 1 else ''

    @property
    def completion_percentage(self):
        fields = [
            self.date_of_birth, self.gender, self.blood_group,
            self.personal_phone, self.current_address, self.designation,
            self.bank_name, self.account_number, self.pan_number,
            self.father_name, self.emergency_contact_phone,
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)


class Education(models.Model):
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, related_name='education')
    degree = models.CharField(max_length=100)
    college_name = models.CharField(max_length=200)
    year_of_passing = models.PositiveIntegerField()
    field_of_study = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.degree} - {self.college_name} ({self.year_of_passing})"


class Certification(models.Model):
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, related_name='certifications')
    name = models.CharField(max_length=200)
    platform = models.CharField(max_length=100)
    issued_date = models.DateField(blank=True, null=True)
    credential_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.platform}"
