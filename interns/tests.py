from django.test import TestCase, Client
from django.urls import reverse
from .models import Intern, Project

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
