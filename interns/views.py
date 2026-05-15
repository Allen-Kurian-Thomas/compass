from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    InternRegistrationForm, InternLoginForm,
    PersonalInfoForm, ContactInfoForm, ProfessionalInfoForm,
    FinancialInfoForm, StatutoryInfoForm, FamilyInfoForm,
    EducationForm, CertificationForm, UpdateProfileForm,
)
from .models import Intern, Education, Certification


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = InternRegistrationForm(request.POST)
        if form.is_valid():
            intern = form.save()
            messages.success(
                request,
                f"Account created for {intern.full_name}. Your registration is pending HR approval. "
                f"You will be notified once approved."
            )
            return redirect('login')
    else:
        form = InternRegistrationForm()
    return render(request, 'interns/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = InternLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.full_name.split()[0]}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid email or password. Please try again.")
    else:
        form = InternLoginForm()
    return render(request, 'interns/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('login')


@login_required
@login_required
def home_view(request):
    return render(request, 'interns/home.html')


@login_required
def profile_view(request):
    intern = request.user
    educations = intern.education.all()
    certifications = intern.certifications.all()
    skills = intern.get_skills_list()
    context = {
        'intern': intern,
        'educations': educations,
        'certifications': certifications,
        'skills': skills,
    }
    return render(request, 'interns/profile.html', context)


@login_required
def update_profile_view(request):
    if request.method == 'POST':
        form = UpdateProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
    else:
        form = UpdateProfileForm(instance=request.user)
    
    return render(request, 'interns/update_profile.html', {'form': form})


@login_required
def edit_personal(request):
    if request.method == 'POST':
        form = PersonalInfoForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Personal information updated successfully.")
            return redirect('profile')
    else:
        form = PersonalInfoForm(instance=request.user)
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Personal Information',
        'section_icon': '👤',
    })


@login_required
def edit_contact(request):
    if request.method == 'POST':
        form = ContactInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Contact information updated successfully.")
            return redirect('profile')
    else:
        form = ContactInfoForm(instance=request.user)
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Contact Information',
        'section_icon': '📞',
    })


@login_required
def edit_professional(request):
    if request.method == 'POST':
        form = ProfessionalInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Professional information updated successfully.")
            return redirect('profile')
    else:
        form = ProfessionalInfoForm(instance=request.user)
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Professional Information',
        'section_icon': '💼',
    })


@login_required
def edit_financial(request):
    if request.method == 'POST':
        form = FinancialInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Financial information updated successfully.")
            return redirect('profile')
    else:
        form = FinancialInfoForm(instance=request.user)
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Financial Information',
        'section_icon': '🏦',
    })


@login_required
def edit_statutory(request):
    if request.method == 'POST':
        form = StatutoryInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Statutory information updated successfully.")
            return redirect('profile')
    else:
        form = StatutoryInfoForm(instance=request.user)
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Statutory Information',
        'section_icon': '📋',
    })


@login_required
def edit_family(request):
    if request.method == 'POST':
        form = FamilyInfoForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Family information updated successfully.")
            return redirect('profile')
    else:
        form = FamilyInfoForm(instance=request.user)
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Family & Emergency Contacts',
        'section_icon': '👨‍👩‍👧‍👦',
    })


@login_required
def add_education(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            edu = form.save(commit=False)
            edu.intern = request.user
            edu.save()
            messages.success(request, "Education record added.")
            return redirect('profile')
    else:
        form = EducationForm()
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Add Education',
        'section_icon': '🎓',
    })


@login_required
def delete_education(request, pk):
    edu = get_object_or_404(Education, pk=pk, intern=request.user)
    edu.delete()
    messages.success(request, "Education record removed.")
    return redirect('profile')


@login_required
def add_certification(request):
    if request.method == 'POST':
        form = CertificationForm(request.POST)
        if form.is_valid():
            cert = form.save(commit=False)
            cert.intern = request.user
            cert.save()
            messages.success(request, "Certification added.")
            return redirect('profile')
    else:
        form = CertificationForm()
    return render(request, 'interns/profile_edit.html', {
        'form': form,
        'section': 'Add Certification',
        'section_icon': '🏆',
    })


@login_required
def delete_certification(request, pk):
    cert = get_object_or_404(Certification, pk=pk, intern=request.user)
    cert.delete()
    messages.success(request, "Certification removed.")
    return redirect('profile')
