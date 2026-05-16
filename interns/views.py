from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import views as auth_views
from django.views.generic import (
    TemplateView, FormView, UpdateView, CreateView, DeleteView, View
)
from django.urls import reverse_lazy
from django.contrib import messages
from .forms import (
    InternRegistrationForm, InternLoginForm,
    PersonalInfoForm, ContactInfoForm, ProfessionalInfoForm,
    FinancialInfoForm, StatutoryInfoForm, FamilyInfoForm,
    EducationForm, CertificationForm, UpdateProfileForm,
)
from .models import Intern, Education, Certification


class RegisterView(FormView):
    template_name = 'interns/register.html'
    form_class = InternRegistrationForm
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        intern = form.save()
        return super().form_valid(form)


class LoginView(auth_views.LoginView):
    template_name = 'interns/login.html'
    authentication_form = InternLoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect('home')

    def form_invalid(self, form):
        messages.error(self.request, "Invalid email or password. Please try again.")
        return super().form_invalid(form)


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'interns/home.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'interns/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        intern = self.request.user
        context.update({
            'intern': intern,
            'educations': intern.education.all(),
            'certifications': intern.certifications.all(),
            'skills': intern.get_skills_list(),
        })
        return context


class UpdateProfileView(LoginRequiredMixin, UpdateView):
    template_name = 'interns/update_profile.html'
    form_class = UpdateProfileForm
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        return super().form_valid(form)


class BaseProfileEditView(LoginRequiredMixin, UpdateView):
    template_name = 'interns/profile_edit.html'
    success_url = reverse_lazy('profile')
    section = ""
    section_icon = ""

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': self.section,
            'section_icon': self.section_icon,
        })
        return context

    def form_valid(self, form):
        return super().form_valid(form)


class EditPersonalView(BaseProfileEditView):
    form_class = PersonalInfoForm
    section = 'Personal Information'
    section_icon = '👤'


class EditContactView(BaseProfileEditView):
    form_class = ContactInfoForm
    section = 'Contact Information'
    section_icon = '📞'


class EditProfessionalView(BaseProfileEditView):
    form_class = ProfessionalInfoForm
    section = 'Professional Information'
    section_icon = '💼'


class EditFinancialView(BaseProfileEditView):
    form_class = FinancialInfoForm
    section = 'Financial Information'
    section_icon = '🏦'


class EditStatutoryView(BaseProfileEditView):
    form_class = StatutoryInfoForm
    section = 'Statutory Information'
    section_icon = '📋'


class EditFamilyView(BaseProfileEditView):
    form_class = FamilyInfoForm
    section = 'Family & Emergency Contacts'
    section_icon = '👨‍👩‍👧‍👦'


class AddEducationView(LoginRequiredMixin, CreateView):
    model = Education
    form_class = EducationForm
    template_name = 'interns/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'Add Education',
            'section_icon': '🎓',
        })
        return context

    def form_valid(self, form):
        form.instance.intern = self.request.user
        return super().form_valid(form)


class DeleteEducationView(LoginRequiredMixin, DeleteView):
    model = Education
    success_url = reverse_lazy('profile')

    def get_queryset(self):
        return Education.objects.filter(intern=self.request.user)

    def get(self, request, *args, **kwargs):
        # Allow deletion via GET to maintain compatibility with existing links
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class AddCertificationView(LoginRequiredMixin, CreateView):
    model = Certification
    form_class = CertificationForm
    template_name = 'interns/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'section': 'Add Certification',
            'section_icon': '🏆',
        })
        return context

    def form_valid(self, form):
        form.instance.intern = self.request.user
        return super().form_valid(form)


class DeleteCertificationView(LoginRequiredMixin, DeleteView):
    model = Certification
    success_url = reverse_lazy('profile')

    def get_queryset(self):
        return Certification.objects.filter(intern=self.request.user)

    def get(self, request, *args, **kwargs):
        # Allow deletion via GET to maintain compatibility with existing links
        return self.post(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
