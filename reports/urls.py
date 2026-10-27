from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_list, name='report_list'),
    path('generate/<int:water_test_id>/', views.generate_report, name='generate_report'),
    path('<int:pk>/', views.report_detail, name='report_detail'),
]