from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_client, name='register_client'),
    path('client/login/', views.client_login, name='client_login'),
    path('technician/login/', views.technician_login, name='technician_login'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('logout/', views.user_logout, name='logout'),
    path('redirect/', views.role_redirect, name='role_redirect'),
]
