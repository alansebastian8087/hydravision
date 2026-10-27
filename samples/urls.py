from django.urls import path
from . import views

urlpatterns = [
    path('', views.sample_list, name='sample_list'),
    path('client/dashboard/', views.client_dashboard, name='client_dashboard'),
    path('add/', views.sample_create, name='sample_create'),
    path('<int:pk>/', views.sample_detail, name='sample_detail'),
    path('edit/<int:pk>/', views.sample_update, name='sample_update'),
    path('delete/<int:pk>/', views.sample_delete, name='sample_delete'),
    path('water-tests/', views.water_test_list, name='water_test_list'),
    path('water-tests/add/', views.water_test_create, name='water_test_create'),
    path('test-results/', views.test_result_list, name='test_result_list'),
    path('test-results/add/', views.test_result_create, name='test_result_create'),
    path('process-water-test/<int:pk>/', views.process_water_test, name='process_water_test'),
    path('technician/dashboard/', views.technician_dashboard, name='technician_dashboard'),
    path('technician/requests/', views.sample_requests, name='sample_requests'),
    path('technician/accept/<int:pk>/', views.accept_sample, name='accept_sample'),
    path('technician/result-entry/<int:pk>/', views.enter_test_results, name='enter_test_results'),
    path('technician/history/', views.test_history, name='test_history'),
]