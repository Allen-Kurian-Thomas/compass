from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from cloudinary.models import CloudinaryField
import logging

logger = logging.getLogger(__name__)


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
    # Only look at interns that already have an employee_id assigned
    existing = Intern.objects.filter(
        employee_id__isnull=False
    ).exclude(employee_id='')

    highest_num = 1000
    for intern in existing:
        try:
            num = int(intern.employee_id[2:])
            if num > highest_num:
                highest_num = num
        except (ValueError, TypeError, IndexError):
            continue

    return f"TS{highest_num + 1}"


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
    ROLE_CHOICES = [
        ('intern', 'Intern'),
        ('senior_architect', 'Senior Architect'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='intern')

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
    profile_photo = CloudinaryField('profile_photo', type='private', folder='Compass_profilepic', blank=True, null=True)
    resume = CloudinaryField('resume', type='authenticated', folder='Compass_resume', resource_type='raw', blank=True, null=True)
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

    # Family
    father_name = models.CharField(max_length=150, blank=True)
    mother_name = models.CharField(max_length=150, blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)

    # Registration Payment
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_screenshot = CloudinaryField('payment_screenshot', type='authenticated', folder='Compass_payment', blank=True, null=True)

    # Technical skills (stored as comma-separated tags)
    technical_skills = models.TextField(blank=True, help_text="Comma-separated skills e.g. Python, Django")

    # Education & Certifications Summary (for Profile Update)
    highest_degree = models.CharField(max_length=150, blank=True)
    college_university = models.CharField(max_length=200, blank=True)
    graduation_year = models.CharField(max_length=10, blank=True)
    certifications_summary = models.TextField(blank=True, help_text="Comma separated certifications")

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
        if self.role == 'admin':
            self.is_staff = True
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

    @property
    def payment_screenshot_url(self):
        """Generate signed URL for payment screenshot using helper method."""
        if self.payment_screenshot:
            from .cloudinary_helpers import CloudinaryHelper
            try:
                # Try authenticated type first (for new uploads)
                url = CloudinaryHelper.generate_signed_url(
                    self.payment_screenshot.public_id,
                    resource_type='image',
                    type='authenticated'
                )
                if url:
                    return url
            except Exception as e:
                logger.warning(f"Failed to generate authenticated URL for intern {self.email}: {str(e)}")
            
            # Fallback to private type (for existing uploads)
            try:
                url = CloudinaryHelper.generate_signed_url(
                    self.payment_screenshot.public_id,
                    resource_type='image',
                    type='private'
                )
                if url:
                    return url
            except Exception as e:
                logger.warning(f"Failed to generate private URL for intern {self.email}: {str(e)}")
            
            # Final fallback to default URL
            try:
                return self.payment_screenshot.url
            except Exception as e:
                logger.error(f"Failed to get default URL for intern {self.email}: {str(e)}")
                return None
        return None

    @property
    def profile_photo_url(self):
        """Generate signed URL for profile photo using helper method."""
        if self.profile_photo:
            from .cloudinary_helpers import CloudinaryHelper
            try:
                url = CloudinaryHelper.generate_signed_url(
                    self.profile_photo.public_id,
                    resource_type='image',
                    type='private'
                )
                if url:
                    return url
            except Exception as e:
                logger.error(f"Failed to generate signed URL for profile photo for intern {self.email}: {str(e)}")
            # Fallback to default URL if signed URL generation fails
            try:
                return self.profile_photo.url
            except Exception as e:
                logger.error(f"Failed to get default URL for profile photo for intern {self.email}: {str(e)}")
                return None
        return None

    @property
    def resume_url(self):
        """Generate signed URL for resume using helper method."""
        if self.resume:
            # Check if the resume is a Cloudinary resource (has public_id)
            if hasattr(self.resume, 'public_id'):
                from .cloudinary_helpers import CloudinaryHelper
                try:
                    logger.info(f"Attempting to generate signed URL for resume with public_id: {self.resume.public_id}")
                    # Try authenticated type first (for new uploads)
                    url = CloudinaryHelper.generate_signed_url(
                        self.resume.public_id,
                        resource_type='raw',
                        type='authenticated',
                        use_extension=True
                    )
                    if url:
                        logger.info(f"Generated authenticated signed URL for resume for intern {self.email}: {url}")
                        return url
                except Exception as e:
                    logger.warning(f"Failed to generate authenticated URL for resume for intern {self.email}: {str(e)}")

                # Fallback to private type (for existing uploads)
                try:
                    url = CloudinaryHelper.generate_signed_url(
                        self.resume.public_id,
                        resource_type='raw',
                        type='private',
                        use_extension=True
                    )
                    if url:
                        logger.info(f"Generated private signed URL for resume for intern {self.email}: {url}")
                        return url
                except Exception as e:
                    logger.warning(f"Failed to generate private URL for resume for intern {self.email}: {str(e)}")
            else:
                logger.info(f"Resume does not have public_id attribute for intern {self.email}, using default URL")
            # Fallback to default URL (for local files or if signed URL generation fails)
            try:
                default_url = self.resume.url
                logger.info(f"Using default URL for resume for intern {self.email}: {default_url}")
                return default_url
            except Exception as e:
                logger.error(f"Failed to get default URL for resume for intern {self.email}: {str(e)}")
                return None
        else:
            logger.info(f"No resume found for intern {self.email}")
        return None


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


class ProjectAllocation(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='allocations')
    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, related_name='allocations')
    location = models.CharField(max_length=150, blank=True)
    allocation_percentage = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = ('project', 'intern')
        verbose_name = 'Project Allocation'
        verbose_name_plural = 'Project Allocations'

    def __str__(self):
        return f"{self.intern.full_name} - {self.project.name} ({self.allocation_percentage}%)"


class Project(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('finished', 'Finished'),
        ('abandoned', 'Abandoned'),
    ]
    PROJECT_TYPE_CHOICES = [
        ('internal', 'Internal'),
        ('external', 'External'),
    ]

    name = models.CharField(max_length=200)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='internal')
    client_department = models.CharField(max_length=200, blank=True)
    lead = models.ForeignKey(Intern, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_projects')
    allocated_interns = models.ManyToManyField(Intern, through='ProjectAllocation', related_name='allocated_projects', blank=True)
    project_category = models.CharField(max_length=100, blank=True)
    tech_stack = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class RejectedCandidate(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_screenshot = CloudinaryField('payment_screenshot', type='authenticated', folder='Compass_payment', blank=True, null=True)
    date_joined = models.DateTimeField()
    date_rejected = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rejected Candidate'
        verbose_name_plural = 'Rejected Candidates'
        ordering = ['-date_rejected']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    @property
    def payment_screenshot_url(self):
        """Generate signed URL for payment screenshot using helper method."""
        if self.payment_screenshot:
            from .cloudinary_helpers import CloudinaryHelper
            try:
                # Try authenticated type first (for new uploads)
                url = CloudinaryHelper.generate_signed_url(
                    self.payment_screenshot.public_id,
                    resource_type='image',
                    type='authenticated'
                )
                if url:
                    return url
            except Exception as e:
                logger.warning(f"Failed to generate authenticated URL for rejected candidate {self.email}: {str(e)}")
            
            # Fallback to private type (for existing uploads)
            try:
                url = CloudinaryHelper.generate_signed_url(
                    self.payment_screenshot.public_id,
                    resource_type='image',
                    type='private'
                )
                if url:
                    return url
            except Exception as e:
                logger.warning(f"Failed to generate private URL for rejected candidate {self.email}: {str(e)}")
            
            # Final fallback to default URL
            try:
                return self.payment_screenshot.url
            except Exception as e:
                logger.error(f"Failed to get default URL for rejected candidate {self.email}: {str(e)}")
                return None
        return None


class ProgressReport(models.Model):
    ROLE_CHOICES = [
        ('designer', 'Designer'),
        ('developer', 'Developer'),
        ('tester', 'Tester'),
        ('manager', 'Manager'),
        ('other', 'Other'),
    ]

    intern = models.ForeignKey(Intern, on_delete=models.CASCADE, related_name='progress_reports')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='progress_reports')
    report_date = models.DateField(default=timezone.now)
    hours_worked = models.DecimalField(decimal_places=2, max_digits=5)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='developer')
    technology_stack = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Progress Report'
        verbose_name_plural = 'Progress Reports'
        ordering = ['-report_date', '-created_at']

    def __str__(self):
        return f"{self.intern.full_name} - {self.project.name} ({self.report_date})"
