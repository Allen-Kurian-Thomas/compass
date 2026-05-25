from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import views as auth_views
from django.conf import settings
import urllib.parse
from django.views.generic import (
    TemplateView, FormView, UpdateView, CreateView, DeleteView, View
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import (
    InternRegistrationForm, InternLoginForm,
    PersonalInfoForm, ContactInfoForm, ProfessionalInfoForm,
    FinancialInfoForm, StatutoryInfoForm, FamilyInfoForm,
    EducationForm, CertificationForm, UpdateProfileForm,
)
from .models import Intern, Education, Certification, DEPARTMENT_CHOICES, Project, RejectedCandidate
from django.http import JsonResponse

class CheckEmailView(View):
    def get(self, request, *args, **kwargs):
        email = request.GET.get('email', '').strip()
        exists = False
        if email:
            exists = Intern.objects.filter(email__iexact=email).exists()
        return JsonResponse({'exists': exists})


class RegisterView(FormView):
    template_name = 'interns/register.html'
    form_class = InternRegistrationForm
    success_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        upi_id = getattr(settings, 'UPI_ID', 'smohammedshafeeqhameed@oksbi')
        upi_name = getattr(settings, 'UPI_NAME', 's mohammed shafeeq hameed')
        # Build the UPI payment URI
        upi_uri = f"upi://pay?pa={upi_id}&pn={upi_name}&am=3000&cu=INR&tn=Registration Fee&mc=0000"
        # URL encode the entire UPI URI for the QR code generation service
        encoded_upi_uri = urllib.parse.quote(upi_uri)
        context['upi_id'] = upi_id
        context['upi_name'] = upi_name
        context['qr_code_url'] = f"https://api.qrserver.com/v1/create-qr-code/?size=180x180&data={encoded_upi_uri}"
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        intern = form.save(commit=False)
        # Manually extract fields from POST/FILES since they aren't in the form class
        intern.transaction_id = self.request.POST.get('transaction_id', '')
        if 'payment_screenshot' in self.request.FILES:
            intern.payment_screenshot = self.request.FILES['payment_screenshot']
        intern.save()
        messages.success(self.request, "Registration successful! Your account is pending admin approval.")
        return super().form_valid(form)


class LoginView(auth_views.LoginView):
    template_name = 'interns/login.html'
    authentication_form = InternLoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff or request.user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        if user.is_staff or user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('home')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'interns/home.html'


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'interns/admin_dashboard.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mocking active projects since there is no Project model yet
        context['active_projects'] = 45
        context['total_employees'] = Intern.objects.filter(status='approved', is_staff=False).count()
        context['recent_requests'] = Intern.objects.filter(status='pending').order_by('-date_joined')[:5]
        return context


class AdminEmployeeApprovalView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'interns/employee_approval.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = Intern.objects.filter(status='pending', is_staff=False).order_by('-date_joined')
        
        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(transaction_id__icontains=search_query)
            )
            
        # Pagination functionality
        paginator = Paginator(queryset, 10)  # Show 10 requests per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['pending_interns'] = page_obj
        context['page_obj'] = page_obj
        context['search_query'] = search_query
        context['total_count'] = queryset.count()
        return context


class AdminEmployeeActionView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, pk, action):
        intern = get_object_or_404(Intern, pk=pk)
        if action == 'approve':
            intern.status = 'approved'
            intern.save()
        elif action == 'reject':
            RejectedCandidate.objects.create(
                full_name=intern.full_name,
                email=intern.email,
                department=intern.department,
                transaction_id=intern.transaction_id,
                payment_screenshot=intern.payment_screenshot,
                date_joined=intern.date_joined
            )
            intern.delete()
        return redirect('employee_approval')


class AdminEmployeeListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'interns/employee_list.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = Intern.objects.filter(status='approved', is_staff=False).order_by('-date_joined')
        
        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )
            
        # Department filter
        department_query = self.request.GET.get('department', '')
        if department_query:
            queryset = queryset.filter(department=department_query)
            
        # Status filter (using is_active)
        status_query = self.request.GET.get('status', '')
        if status_query == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_query == 'inactive':
            queryset = queryset.filter(is_active=False)
            
        # Pagination functionality
        paginator = Paginator(queryset, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['approved_interns'] = page_obj
        context['page_obj'] = page_obj
        context['search_query'] = search_query
        context['department_query'] = department_query
        context['status_query'] = status_query
        context['departments'] = DEPARTMENT_CHOICES
        context['total_count'] = queryset.count()
        return context

class AdminRejectedRegistrationsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'interns/rejected_registrations.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        queryset = RejectedCandidate.objects.all().order_by('-date_rejected')

        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(transaction_id__icontains=search_query)
            )

        # Pagination
        paginator = Paginator(queryset, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context['rejected_interns'] = page_obj
        context['page_obj'] = page_obj
        context['search_query'] = search_query
        context['total_count'] = queryset.count()
        return context


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


class AdminProjectListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'interns/project_list.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = Project.objects.all().select_related('lead').order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(client_department__icontains=search_query) |
                Q(lead__first_name__icontains=search_query) |
                Q(lead__last_name__icontains=search_query)
            )
            
        # Status filter
        status_query = self.request.GET.get('status', '')
        if status_query:
            queryset = queryset.filter(status=status_query)
            
        # Pagination functionality
        paginator = Paginator(queryset, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['projects'] = page_obj
        context['page_obj'] = page_obj
        context['search_query'] = search_query
        context['status_query'] = status_query
        context['total_count'] = queryset.count()
        return context
