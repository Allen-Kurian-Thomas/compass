from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Intern, Education, Certification


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 0


@admin.register(Intern)
class InternAdmin(UserAdmin):
    model = Intern
    list_display = ('email', 'full_name', 'employee_id', 'department', 'status', 'date_of_joining', 'is_active')
    list_filter = ('status', 'department', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name', 'employee_id')
    ordering = ('-date_joined',)
    inlines = [EducationInline, CertificationInline]

    fieldsets = (
        ('Account', {'fields': ('email', 'password', 'status', 'employee_id')}),
        ('Personal', {'fields': ('full_name', 'date_of_birth', 'gender', 'blood_group', 'marital_status', 'profile_photo', 'bio')}),
        ('Contact', {'fields': ('personal_phone', 'skype_id', 'current_address', 'permanent_address')}),
        ('Professional', {'fields': ('department', 'designation', 'reporting_manager', 'primary_unit', 'total_experience', 'date_of_joining', 'technical_skills')}),
        ('Financial', {'fields': ('bank_name', 'account_number', 'ifsc_code', 'pan_number', 'aadhaar_number')}),
        ('Statutory', {'fields': ('pf_uan', 'pf_account_number', 'passport_number')}),
        ('Family', {'fields': ('father_name', 'mother_name', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'department', 'password1', 'password2', 'status'),
        }),
    )


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('intern', 'degree', 'college_name', 'year_of_passing')
    search_fields = ('intern__email', 'intern__full_name', 'degree', 'college_name')


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('intern', 'name', 'platform', 'issued_date')
    search_fields = ('intern__email', 'name', 'platform')
