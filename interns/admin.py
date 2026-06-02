from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Intern, Education, Certification, Project, ProjectAllocation


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class CertificationInline(admin.TabularInline):
    model = Certification
    extra = 0


@admin.register(Intern)
class InternAdmin(UserAdmin):
    model = Intern
    list_display = ('email', 'full_name', 'role', 'employee_id', 'department', 'status', 'date_of_joining', 'is_active')
    list_filter = ('role', 'status', 'department', 'is_active', 'is_staff')
    search_fields = ('email', 'full_name', 'employee_id')
    ordering = ('-date_joined',)
    inlines = [EducationInline, CertificationInline]

    fieldsets = (
        ('Account', {'fields': ('email', 'password', 'status', 'employee_id')}),
        ('Personal', {'fields': ('full_name', 'date_of_birth', 'gender', 'blood_group', 'marital_status', 'profile_photo', 'bio')}),
        ('Contact', {'fields': ('personal_phone', 'skype_id', 'current_address', 'permanent_address')}),
        ('Professional', {'fields': ('department', 'designation', 'reporting_manager', 'primary_unit', 'total_experience', 'date_of_joining', 'technical_skills')}),
        ('Financial', {'fields': ('bank_name', 'account_number', 'ifsc_code', 'pan_number', 'aadhaar_number')}),
        ('Family', {'fields': ('father_name', 'mother_name', 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'department', 'password1', 'password2', 'status', 'role'),
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


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_type', 'client_department', 'lead', 'status', 'created_at')
    list_filter = ('project_type', 'status')
    search_fields = ('name', 'client_department')


@admin.register(ProjectAllocation)
class ProjectAllocationAdmin(admin.ModelAdmin):
    list_display = ('project', 'intern', 'location', 'allocation_percentage')
    list_filter = ('project', 'location')
    search_fields = ('intern__full_name', 'intern__email', 'project__name')
