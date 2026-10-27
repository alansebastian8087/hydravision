from django.shortcuts import render

from customers.models import Customer
from samples.models import Sample, WaterTest
from reports.models import Report
from payments.models import Payment
from accounts.decorators import role_required


@role_required('Admin')
def dashboard_home(request):
    total_customers = Customer.objects.count()
    total_samples = Sample.objects.count()
    total_water_tests = WaterTest.objects.count()
    total_reports = Report.objects.count()
    total_payments = Payment.objects.count()

    paid_payments = Payment.objects.filter(
        payment_status='Paid'
    ).count()

    pending_payments = Payment.objects.filter(
        payment_status='Pending'
    ).count()

    summer_samples = Sample.objects.filter(
        season='Summer'
    ).count()

    monsoon_samples = Sample.objects.filter(
        season='Monsoon'
    ).count()

    winter_samples = Sample.objects.filter(
        season='Winter'
    ).count()

    completed_samples = Sample.objects.filter(
        sample_status='Completed'
    ).count()

    testing_samples = Sample.objects.filter(
        sample_status='Testing'
    ).count()

    pending_samples = Sample.objects.filter(
        sample_status='Pending'
    ).count()

    generated_reports = Sample.objects.filter(
        sample_status='Report Generated'
    ).count()

    context = {
        'total_customers': total_customers,
        'total_samples': total_samples,
        'total_water_tests': total_water_tests,
        'total_reports': total_reports,
        'total_payments': total_payments,
        'paid_payments': paid_payments,
        'pending_payments': pending_payments,
        'summer_samples': summer_samples,
        'monsoon_samples': monsoon_samples,
        'winter_samples': winter_samples,
        'completed_samples': completed_samples,
        'testing_samples': testing_samples,
        'pending_samples': pending_samples,
        'generated_reports': generated_reports,
    }

    return render(request, 'dashboard/dashboard_home.html', context)