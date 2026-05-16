from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('home/', views.HomeView.as_view(), name='home'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('profile/edit/personal/', views.EditPersonalView.as_view(), name='edit_personal'),
    path('profile/edit/contact/', views.EditContactView.as_view(), name='edit_contact'),
    path('profile/edit/professional/', views.EditProfessionalView.as_view(), name='edit_professional'),
    path('profile/edit/financial/', views.EditFinancialView.as_view(), name='edit_financial'),
    path('profile/edit/statutory/', views.EditStatutoryView.as_view(), name='edit_statutory'),
    path('profile/edit/family/', views.EditFamilyView.as_view(), name='edit_family'),
    path('profile/education/add/', views.AddEducationView.as_view(), name='add_education'),
    path('profile/education/delete/<int:pk>/', views.DeleteEducationView.as_view(), name='delete_education'),
    path('profile/certification/add/', views.AddCertificationView.as_view(), name='add_certification'),
    path('profile/certification/delete/<int:pk>/', views.DeleteCertificationView.as_view(), name='delete_certification'),
]
