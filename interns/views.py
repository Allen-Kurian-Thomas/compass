from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import views as auth_views
from django.conf import settings
import urllib.parse
import logging
from django.views.generic import (
    TemplateView, FormView, UpdateView, CreateView, DeleteView, View, DetailView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import (
    InternRegistrationForm, InternLoginForm,
    PersonalInfoForm, ContactInfoForm, ProfessionalInfoForm,
    FinancialInfoForm, FamilyInfoForm,
    EducationForm, CertificationForm, UpdateProfileForm,
    ProgressReportForm,
)
from .models import Intern, Education, Certification, DEPARTMENT_CHOICES, Project, RejectedCandidate, ProgressReport
from .cloudinary_helpers import CloudinaryHelper
from django.http import JsonResponse

logger = logging.getLogger(__name__)

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
            try:
                # CloudinaryField will handle upload automatically with type='authenticated' and folder='Compass_payment'
                intern.payment_screenshot = self.request.FILES['payment_screenshot']
                logger.info(f"Payment screenshot upload initiated for {intern.email}")
            except Exception as e:
                logger.error(f"Error assigning payment screenshot for {intern.email}: {str(e)}")
                messages.error(self.request, "An error occurred while processing the payment screenshot.")
                return self.form_invalid(form)
        intern.save()
        messages.success(self.request, "Registration successful! Your account is pending admin approval.")
        return super().form_valid(form)


class LoginView(auth_views.LoginView):
    template_name = 'interns/login.html'
    authentication_form = InternLoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.role == 'senior_architect':
                return redirect('architect_dashboard')
            if request.user.is_staff or request.user.is_superuser or request.user.role == 'admin':
                return redirect('admin_dashboard')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        if user.role == 'senior_architect':
            return redirect('architect_dashboard')
        if user.is_staff or user.is_superuser or user.role == 'admin':
            return redirect('admin_dashboard')
        return redirect('home')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'interns/home.html'


class MyProjectsView(LoginRequiredMixin, TemplateView):
    template_name = 'interns/my_projects.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import ProjectAllocation
        allocations = (
            ProjectAllocation.objects
            .filter(intern=self.request.user)
            .select_related('project', 'project__lead')
            .order_by('project__status', 'project__name')
        )
        context['allocations'] = allocations
        return context


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'interns/admin_dashboard.html'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'admin'

    def handle_no_permission(self):
        if self.request.user.is_authenticated and self.request.user.role == 'senior_architect':
            return redirect('architect_dashboard')
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_projects'] = Project.objects.filter(status='active').count()
        context['total_employees'] = Intern.objects.filter(status='approved', is_staff=False).count()
        context['recent_requests'] = Intern.objects.filter(status='pending').order_by('-date_joined')[:5]
        context['departments'] = DEPARTMENT_CHOICES
        context['available_interns'] = Intern.objects.filter(status='approved', is_staff=False)
        context['recent_projects'] = Project.objects.all().select_related('lead').order_by('-created_at')[:5]
        return context


class ArchitectDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'interns/admin_dashboard.html'

    def test_func(self):
        return self.request.user.role == 'senior_architect'

    def handle_no_permission(self):
        if self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'admin'):
            return redirect('admin_dashboard')
        return super().handle_no_permission()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_projects'] = Project.objects.filter(status='active').count()
        context['total_employees'] = Intern.objects.filter(status='approved', is_staff=False).count()
        context['departments'] = DEPARTMENT_CHOICES
        context['available_interns'] = Intern.objects.filter(status='approved', is_staff=False)
        context['recent_projects'] = Project.objects.all().select_related('lead').order_by('-created_at')[:5]
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
            logger.info(f"Intern {intern.email} approved by admin")
        elif action == 'reject':
            try:
                # Copy payment screenshot if it exists
                payment_screenshot = None
                if intern.payment_screenshot:
                    payment_screenshot = intern.payment_screenshot
                    logger.info(f"Copying payment screenshot for rejected candidate {intern.email}")
                
                RejectedCandidate.objects.create(
                    full_name=intern.full_name,
                    email=intern.email,
                    department=intern.department,
                    transaction_id=intern.transaction_id,
                    payment_screenshot=payment_screenshot,
                    date_joined=intern.date_joined
                )
                intern.delete()
                logger.info(f"Intern {intern.email} rejected and moved to RejectedCandidate")
                messages.success(request, f"{intern.full_name} has been rejected.")
            except Exception as e:
                logger.error(f"Error rejecting intern {intern.email}: {str(e)}")
                messages.error(request, "An error occurred while rejecting the candidate.")
                return redirect('employee_approval')
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


class AdminInternDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Intern
    template_name = 'interns/admin_intern_detail.html'
    context_object_name = 'intern'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser


class AdminAddEmployeeView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        import re
        from django.utils.dateparse import parse_date

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        date_of_joining_str = request.POST.get('date_of_joining', '').strip()
        department = request.POST.get('department', '').strip()
        role = request.POST.get('role', 'intern').strip()

        errors = {}

        if not full_name:
            errors['full_name'] = "Full name is required."
        elif len(full_name) > 150:
            errors['full_name'] = "Full name cannot exceed 150 characters."

        if not email:
            errors['email'] = "Email is required."
        elif Intern.objects.filter(email__iexact=email).exists():
            errors['email'] = "An employee with this email already exists."

        if not password:
            errors['password'] = "Password is required."
        elif len(password) < 8:
            errors['password'] = "Password must be at least 8 characters long."
        else:
            if not re.search(r'[A-Z]', password):
                errors['password'] = "Password must contain at least one uppercase letter."
            elif not re.search(r'[0-9]', password):
                errors['password'] = "Password must contain at least one number."
            elif not re.search(r'[^a-zA-Z0-9]', password):
                errors['password'] = "Password must contain at least one special character."

        date_of_joining = None
        if not date_of_joining_str:
            errors['date_of_joining'] = "Date of joining is required."
        else:
            date_of_joining = parse_date(date_of_joining_str)
            if not date_of_joining:
                errors['date_of_joining'] = "Invalid date format. Use YYYY-MM-DD."

        valid_departments = [choice[0] for choice in DEPARTMENT_CHOICES]
        if not department:
            errors['department'] = "Department is required."
        elif department not in valid_departments:
            errors['department'] = "Selected department is invalid."

        valid_roles = [choice[0] for choice in Intern.ROLE_CHOICES]
        if role not in valid_roles:
            errors['role'] = "Selected role is invalid."

        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        try:
            user = Intern.objects.create_user(
                email=email,
                full_name=full_name,
                password=password,
                department=department,
                date_of_joining=date_of_joining,
                status='approved',
                role=role
            )
            return JsonResponse({'success': True, 'message': 'Employee added successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': {'non_field_errors': str(e)}}, status=500)

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
        try:
            # CloudinaryField will handle upload automatically with type='private' and folder='Compass_profilepic'
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error updating profile for {self.request.user.email}: {str(e)}")
            messages.error(self.request, "An error occurred while updating your profile. Please try again.")
            return self.form_invalid(form)


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
        try:
            # CloudinaryField will handle upload automatically with type='private' and folder='Compass_profilepic'
            return super().form_valid(form)
        except Exception as e:
            logger.error(f"Error updating profile section {self.section} for {self.request.user.email}: {str(e)}")
            messages.error(self.request, "An error occurred while updating your profile. Please try again.")
            return self.form_invalid(form)


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
        return self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'senior_architect'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = Project.objects.all().select_related('lead').order_by('-created_at')
        
        # Search functionality
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(client_department__icontains=search_query) |
                Q(lead__full_name__icontains=search_query)
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
        context['available_interns'] = Intern.objects.filter(status='approved', is_staff=False)
        return context

class AdminAddProjectView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'senior_architect'

    def get(self, request, *args, **kwargs):
        available_interns = Intern.objects.filter(status='approved', is_staff=False)
        return render(request, 'interns/create_project.html', {
            'available_interns': available_interns
        })

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        project_type = request.POST.get('project_type', 'internal').strip()
        client_department = request.POST.get('client_department', '').strip()
        project_category = request.POST.get('project_category', '').strip()
        tech_stack = request.POST.get('tech_stack', '').strip()
        description = request.POST.get('description', '').strip()
        status = request.POST.get('status', 'active').strip()
        allocated_intern_ids = request.POST.getlist('allocated_interns')

        # Check if this is an AJAX request (from old modal usage)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = {}
            if not name:
                errors['name'] = "Project name is required."
            if errors:
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            try:
                project = Project.objects.create(
                    name=name,
                    project_type=project_type,
                    client_department=client_department,
                    project_category=project_category,
                    tech_stack=tech_stack,
                )
                if allocated_intern_ids:
                    from .models import ProjectAllocation
                    for intern_id in allocated_intern_ids:
                        location = request.POST.get(f'location_{intern_id}', '').strip()
                        percentage_str = request.POST.get(f'percentage_{intern_id}', '100').strip()
                        try:
                            percentage = int(percentage_str)
                        except ValueError:
                            percentage = 100
                        ProjectAllocation.objects.create(
                            project=project,
                            intern_id=intern_id,
                            location=location,
                            allocation_percentage=percentage
                        )
                return JsonResponse({'success': True, 'message': 'Project created successfully!'})
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'non_field_errors': str(e)}}, status=500)

        # Standard form POST (page-based)
        form_errors = []
        if not name:
            form_errors.append("Project name is required.")

        if form_errors:
            available_interns = Intern.objects.filter(status='approved', is_staff=False)
            return render(request, 'interns/create_project.html', {
                'available_interns': available_interns,
                'form_errors': form_errors,
            })

        try:
            project = Project.objects.create(
                name=name,
                project_type=project_type,
                client_department=client_department,
                project_category=project_category,
                tech_stack=tech_stack,
            )
            if allocated_intern_ids:
                from .models import ProjectAllocation
                for intern_id in allocated_intern_ids:
                    location = request.POST.get(f'location_{intern_id}', '').strip()
                    percentage_str = request.POST.get(f'percentage_{intern_id}', '100').strip()
                    try:
                        percentage = int(percentage_str)
                    except ValueError:
                        percentage = 100
                    ProjectAllocation.objects.create(
                        project=project,
                        intern_id=intern_id,
                        location=location,
                        allocation_percentage=percentage
                    )
            messages.success(request, f'Project "{name}" created successfully!')
            return redirect('project_list')
        except Exception as e:
            available_interns = Intern.objects.filter(status='approved', is_staff=False)
            return render(request, 'interns/create_project.html', {
                'available_interns': available_interns,
                'form_errors': [str(e)],
            })

class AdminProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project
    template_name = 'interns/project_detail.html'
    context_object_name = 'project'

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'senior_architect'


class AdminEditProjectView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'senior_architect'

    def get(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        available_interns = Intern.objects.filter(status='approved', is_staff=False)
        return render(request, 'interns/edit_project.html', {
            'project': project,
            'available_interns': available_interns,
        })

    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)

        name = request.POST.get('name', '').strip()
        project_type = request.POST.get('project_type', 'internal').strip()
        client_department = request.POST.get('client_department', '').strip()
        project_category = request.POST.get('project_category', '').strip()
        tech_stack = request.POST.get('tech_stack', '').strip()
        status = request.POST.get('status', project.status).strip()
        lead_id = request.POST.get('lead', '').strip()
        allocated_intern_ids = request.POST.getlist('allocated_interns')

        errors = {}
        if not name:
            errors['name'] = 'Project name is required.'

        valid_statuses = [s[0] for s in Project.STATUS_CHOICES]
        if status not in valid_statuses:
            errors['status'] = 'Invalid status selected.'

        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400)

        try:
            project.name = name
            project.project_type = project_type
            project.client_department = client_department
            project.project_category = project_category
            project.tech_stack = tech_stack
            project.status = status

            if lead_id:
                project.lead = get_object_or_404(Intern, pk=lead_id)
            else:
                project.lead = None

            project.save()

            from .models import ProjectAllocation
            # Delete allocations that are no longer selected
            ProjectAllocation.objects.filter(project=project).exclude(intern_id__in=allocated_intern_ids).delete()
            
            # Create or update selected allocations
            for intern_id in allocated_intern_ids:
                location = request.POST.get(f'location_{intern_id}', '').strip()
                percentage_str = request.POST.get(f'percentage_{intern_id}', '100').strip()
                try:
                    percentage = int(percentage_str)
                except ValueError:
                    percentage = 100
                
                ProjectAllocation.objects.update_or_create(
                    project=project,
                    intern_id=intern_id,
                    defaults={
                        'location': location,
                        'allocation_percentage': percentage
                    }
                )

            return JsonResponse({'success': True, 'message': 'Project updated successfully!', 'redirect': '/admin-projects/'})
        except Exception as e:
            return JsonResponse({'success': False, 'errors': {'non_field_errors': str(e)}}, status=500)


class AdminDeleteProjectView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser or self.request.user.role == 'senior_architect'

    def post(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" has been deleted.')
        if request.user.role == 'senior_architect':
            return redirect('architect_project_list')
        return redirect('project_list')


class SubmitEODView(LoginRequiredMixin, CreateView):
    model = ProgressReport
    form_class = ProgressReportForm
    template_name = 'interns/progress_report.html'
    success_url = reverse_lazy('submit_eod')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter projects to only show active ones allocated to this intern,
        # or all active projects if they aren't allocated to any.
        intern = self.request.user
        allocated_projects = Project.objects.filter(allocations__intern=intern, status='active')
        if allocated_projects.exists():
            form.fields['project'].queryset = allocated_projects
        else:
            form.fields['project'].queryset = Project.objects.filter(status='active')
        
        # Override project empty label
        form.fields['project'].empty_label = "Select active project"
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # List of past progress reports submitted by this user
        reports_list = ProgressReport.objects.filter(intern=self.request.user).order_by('-report_date', '-created_at')
        
        # Pagination
        paginator = Paginator(reports_list, 5) # Show 5 reports per page
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['reports'] = page_obj
        context['page_obj'] = page_obj
        return context

    def form_valid(self, form):
        form.instance.intern = self.request.user
        messages.success(self.request, "Progress report submitted successfully!")
        return super().form_valid(form)


class SearchEmployeesView(LoginRequiredMixin, UserPassesTestMixin, View):
    """AJAX endpoint: returns JSON list of approved employees matching search criteria."""

    def test_func(self):
        return (
            self.request.user.is_staff
            or self.request.user.is_superuser
            or self.request.user.role == 'senior_architect'
        )

    def get(self, request, *args, **kwargs):
        q = request.GET.get('q', '').strip()
        role_filter = request.GET.get('role', '').strip()
        location_filter = request.GET.get('location', '').strip()

        queryset = Intern.objects.filter(status='approved', is_staff=False).order_by('full_name')

        if q:
            queryset = queryset.filter(
                Q(full_name__icontains=q) | Q(email__icontains=q) | Q(employee_id__icontains=q)
            )

        if role_filter:
            queryset = queryset.filter(
                Q(designation__icontains=role_filter) | Q(department__icontains=role_filter)
            )

        if location_filter:
            queryset = queryset.filter(current_address__icontains=location_filter)

        results = []
        for intern in queryset[:30]:
            # Build a short location label from current_address
            location_label = ''
            if intern.current_address:
                parts = [p.strip() for p in intern.current_address.split(',') if p.strip()]
                location_label = ', '.join(parts[-2:]) if len(parts) >= 2 else intern.current_address

            results.append({
                'id': intern.id,
                'full_name': intern.full_name,
                'email': intern.email,
                'employee_id': intern.employee_id or '',
                'designation': intern.designation or intern.get_department_display() if hasattr(intern, 'get_department_display') else (intern.department or ''),
                'location': location_label,
                'department': intern.department or '',
            })

        return JsonResponse({'employees': results})
