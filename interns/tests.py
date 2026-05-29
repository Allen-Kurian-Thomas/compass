from django.test import TestCase, Client
from django.urls import reverse
from .models import Intern, Project, ProgressReport, ProjectAllocation

class RolePermissionTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.intern = Intern.objects.create_user(
            email='intern@test.com',
            full_name='Test Intern',
            password='Password123!',
            status='approved',
            role='intern'
        )
        
        self.architect = Intern.objects.create_user(
            email='architect@test.com',
            full_name='Test Architect',
            password='Password123!',
            status='approved',
            role='senior_architect'
        )
        
        self.admin = Intern.objects.create_user(
            email='admin@test.com',
            full_name='Test Admin',
            password='Password123!',
            status='approved',
            role='admin'
        )

    def test_intern_access(self):
        self.client.force_login(self.intern)
        
        # Authenticated users failing UserPassesTestMixin test_func get 403 Forbidden
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 403)

    def test_admin_access(self):
        self.client.force_login(self.admin)
        
        # Admin can access all
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('employee_approval'))
        self.assertEqual(response.status_code, 200)

    def test_architect_access(self):
        self.client.force_login(self.architect)
        
        # Architect can access dashboard & projects
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)
        
        # Architect cannot access employee-related views
        response = self.client.get(reverse('employee_list'))
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(reverse('employee_approval'))
        self.assertEqual(response.status_code, 403)
        
        response = self.client.get(reverse('rejected_registrations'))
        self.assertEqual(response.status_code, 403)

    def test_architect_create_and_edit_project(self):
        self.client.force_login(self.architect)
        
        # Create project with allocations
        response = self.client.post(reverse('admin_add_project'), {
            'name': 'Test Project',
            'project_type': 'internal',
            'client_department': 'R&D',
            'timeline': '3 Months',
            'budget': '5000',
            'allocated_interns': [self.intern.id],
            f'location_{self.intern.id}': 'New York',
            f'percentage_{self.intern.id}': '80'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Project.objects.filter(name='Test Project').exists())
        
        project = Project.objects.get(name='Test Project')
        self.assertEqual(project.allocations.count(), 1)
        allocation = project.allocations.first()
        self.assertEqual(allocation.intern, self.intern)
        self.assertEqual(allocation.location, 'New York')
        self.assertEqual(allocation.allocation_percentage, 80)
        
        # Edit project (and allocate intern with updated details)
        response = self.client.post(reverse('project_edit', kwargs={'pk': project.pk}), {
            'name': 'Test Project Updated',
            'project_type': 'external',
            'client_department': 'Sales',
            'timeline': '6 Months',
            'budget': '10000',
            'allocated_interns': [self.intern.id],
            f'location_{self.intern.id}': 'Bangalore',
            f'percentage_{self.intern.id}': '50'
        }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual(project.name, 'Test Project Updated')
        self.assertEqual(project.project_type, 'external')
        self.assertEqual(project.allocations.count(), 1)
        allocation = project.allocations.first()
        self.assertEqual(allocation.location, 'Bangalore')
        self.assertEqual(allocation.allocation_percentage, 50)


class ProgressReportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.intern = Intern.objects.create_user(
            email='intern@test.com',
            full_name='Test Intern',
            password='Password123!',
            status='approved',
            role='intern'
        )
        self.project_active = Project.objects.create(
            name='Active Project',
            status='active'
        )
        self.project_inactive = Project.objects.create(
            name='Inactive Project',
            status='finished'
        )

    def test_submit_eod_view_requires_login(self):
        response = self.client.get(reverse('submit_eod'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_submit_eod_view_get(self):
        self.client.force_login(self.intern)
        response = self.client.get(reverse('submit_eod'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'interns/progress_report.html')
        self.assertIn('form', response.context)
        self.assertIn('reports', response.context)

    def test_submit_eod_view_post_success(self):
        self.client.force_login(self.intern)
        response = self.client.post(reverse('submit_eod'), {
            'project': self.project_active.id,
            'report_date': '2026-05-29',
            'hours_worked': '8.0',
            'role': 'developer',
            'technology_stack': 'React, Django',
            'description': 'Did some frontend and backend work.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ProgressReport.objects.count(), 1)
        report = ProgressReport.objects.first()
        self.assertEqual(report.intern, self.intern)
        self.assertEqual(report.project, self.project_active)
        self.assertEqual(report.hours_worked, 8.0)
        self.assertEqual(report.role, 'developer')
        self.assertEqual(report.technology_stack, 'React, Django')
        self.assertEqual(report.description, 'Did some frontend and backend work.')

    def test_submit_eod_view_project_filtering(self):
        self.client.force_login(self.intern)
        # When intern has no allocations, they see all active projects in the dropdown
        response = self.client.get(reverse('submit_eod'))
        form = response.context['form']
        project_queryset = form.fields['project'].queryset
        self.assertIn(self.project_active, project_queryset)
        self.assertNotIn(self.project_inactive, project_queryset)

        # Let's allocate intern to self.project_active
        ProjectAllocation.objects.create(
            project=self.project_active,
            intern=self.intern,
            location='WFH',
            allocation_percentage=100
        )
        # Create another active project that this intern is not allocated to
        other_active_project = Project.objects.create(
            name='Other Active Project',
            status='active'
        )

        response = self.client.get(reverse('submit_eod'))
        form = response.context['form']
        project_queryset = form.fields['project'].queryset
        # Now, they should only see self.project_active, not other_active_project because they are allocated to project_active
        self.assertIn(self.project_active, project_queryset)
        self.assertNotIn(other_active_project, project_queryset)

