from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.update_profile_view, name='update_profile'),
    path('profile/edit/contact/', views.edit_contact, name='edit_contact'),
    path('profile/edit/professional/', views.edit_professional, name='edit_professional'),
    path('profile/edit/financial/', views.edit_financial, name='edit_financial'),
    path('profile/edit/statutory/', views.edit_statutory, name='edit_statutory'),
    path('profile/edit/family/', views.edit_family, name='edit_family'),
    path('profile/education/add/', views.add_education, name='add_education'),
    path('profile/education/delete/<int:pk>/', views.delete_education, name='delete_education'),
    path('profile/certification/add/', views.add_certification, name='add_certification'),
    path('profile/certification/delete/<int:pk>/', views.delete_certification, name='delete_certification'),
]
