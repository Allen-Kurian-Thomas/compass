from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Intern, Education, Certification, DEPARTMENT_CHOICES


class InternRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Create a strong password',
            'id': 'id_password1',
        }),
        min_length=8,
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Repeat your password',
            'id': 'id_password2',
        }),
    )

    class Meta:
        model = Intern
        fields = ['full_name', 'email', 'department']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your full name',
                'id': 'id_full_name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'your.name@techyspot.com',
                'id': 'id_email',
            }),
            'department': forms.Select(attrs={
                'class': 'form-input',
                'id': 'id_department',
            }),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class InternLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Official Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'your.name@techyspot.com',
            'autofocus': True,
            'id': 'id_login_email',
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your password',
            'id': 'id_login_password',
        }),
    )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff and not user.is_superuser:
            if user.status == 'pending':
                raise forms.ValidationError(
                    "Your account is pending approval by an administrator.",
                    code='pending_approval',
                )
            elif user.status == 'rejected':
                raise forms.ValidationError(
                    "Your registration request was rejected.",
                    code='rejected',
                )


class PersonalInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Intern
        fields = [
            'date_of_birth', 'gender', 'blood_group', 'marital_status',
            'profile_photo', 'bio',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'gender': forms.Select(attrs={'class': 'form-input'}),
            'blood_group': forms.Select(attrs={'class': 'form-input'}),
            'marital_status': forms.Select(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Brief about yourself...'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-input'}),
        }


class ContactInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Intern
        fields = ['personal_phone', 'skype_id', 'current_address', 'permanent_address']
        widgets = {
            'personal_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+91 XXXXXXXXXX'}),
            'skype_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'live:skype.id'}),
            'current_address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class ProfessionalInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Intern
        fields = ['designation', 'reporting_manager', 'primary_unit', 'total_experience', 'technical_skills']
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Software Engineer Intern'}),
            'reporting_manager': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Manager full name'}),
            'primary_unit': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Backend Team'}),
            'total_experience': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 1 year 6 months'}),
            'technical_skills': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Python, Django, React, PostgreSQL (comma separated)',
            }),
        }


class FinancialInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Intern
        fields = ['bank_name', 'account_number', 'ifsc_code', 'pan_number', 'aadhaar_number']
        widgets = {
            'bank_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Bank name'}),
            'account_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Account number'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'IFSC code'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'PAN number'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Aadhaar number'}),
        }


class StatutoryInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Intern
        fields = ['pf_uan', 'pf_account_number', 'passport_number']
        widgets = {
            'pf_uan': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'PF UAN'}),
            'pf_account_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'PF Account Number'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Passport Number (optional)'}),
        }


class FamilyInfoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Intern
        fields = [
            'father_name', 'mother_name',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
        ]
        widgets = {
            'father_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Father full name'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Mother full name'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Contact name'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Relation (e.g. Spouse)'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Emergency phone number'}),
        }


class UpdateProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Intern
        fields = [
            'date_of_birth', 'gender', 'blood_group', 'marital_status',
            'personal_phone', 'email', 'current_address', 'permanent_address', 'bio',
            'designation', 'primary_unit', 'reporting_manager', 'total_experience',
            'bank_name', 'account_number', 'ifsc_code', 'pan_number', 'aadhaar_number',
            'father_name', 'mother_name', 'emergency_contact_name', 'emergency_contact_relation', 'emergency_contact_phone',
            'pf_uan', 'pf_account_number', 'passport_number', 'technical_skills', 'profile_photo', 'resume',
            'highest_degree', 'college_university', 'graduation_year', 'certifications_summary',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'blood_group': forms.Select(attrs={'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-control'}),
            'personal_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'current_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'permanent_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'designation': forms.TextInput(attrs={'class': 'form-control'}),
            'primary_unit': forms.TextInput(attrs={'class': 'form-control'}),
            'reporting_manager': forms.TextInput(attrs={'class': 'form-control'}),
            'total_experience': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'ifsc_code': forms.TextInput(attrs={'class': 'form-control'}),
            'pan_number': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhaar_number': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'pf_uan': forms.TextInput(attrs={'class': 'form-control'}),
            'pf_account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
            'technical_skills': forms.TextInput(attrs={'class': 'form-control', 'id': 'skills-input'}),
            'profile_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'highest_degree': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Master of Business Administration'}),
            'college_university': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Harvard University'}),
            'graduation_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYY'}),
            'certifications_summary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CFA Level 1, PMP'}),
        }


class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['degree', 'field_of_study', 'college_name', 'year_of_passing']
        widgets = {
            'degree': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. B.Tech, MBA'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Computer Science'}),
            'college_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'College/University name'}),
            'year_of_passing': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '2024'}),
        }


class CertificationForm(forms.ModelForm):
    class Meta:
        model = Certification
        fields = ['name', 'platform', 'issued_date', 'credential_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Certification name'}),
            'platform': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. HackerRank, Coursera'}),
            'issued_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'credential_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...'}),
        }
