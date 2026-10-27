from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from .models import Sample, WaterTest, TestResult
from .forms import SampleForm, WaterTestForm, TestResultForm
from .utils import check_bis_and_wqs
from accounts.decorators import role_required
from customers.models import Customer
from reports.models import Report
from payments.models import Payment


def build_parameter_cards(test_result):
    if not test_result:
        return []

    specs = [
        ("pH", test_result.ph, "6.5 - 8.5", 6.5 <= test_result.ph <= 8.5),
        ("TDS", test_result.tds, "≤ 500 mg/L", test_result.tds <= 500),
        ("Turbidity", test_result.turbidity, "≤ 1 NTU", test_result.turbidity <= 1),
        ("Hardness", test_result.hardness, "≤ 200 mg/L", test_result.hardness <= 200),
        ("Fluoride", test_result.fluoride, "≤ 1.0 mg/L", test_result.fluoride <= 1.0),
        ("Iron", test_result.iron, "≤ 0.3 mg/L", test_result.iron <= 0.3),
        ("Nitrate", test_result.nitrate, "≤ 45 mg/L", test_result.nitrate <= 45),
        ("Chloride", test_result.chloride, "≤ 250 mg/L", test_result.chloride <= 250),
        ("Sulphate", test_result.sulphate, "≤ 200 mg/L", test_result.sulphate <= 200),
        ("Alkalinity", test_result.alkalinity, "≤ 200 mg/L as CaCO₃", test_result.alkalinity <= 200),
    ]

    cards = []

    for name, value, limit, ok in specs:
        cards.append({
            'name': name,
            'value': value,
            'limit': limit,
            'status': 'Good' if ok else 'Needs Attention',
            'ok': ok,
        })

    return cards


def get_payment_for_sample(sample):
    return Payment.objects.filter(sample=sample).order_by('-id').first()


def get_client_result_summary(water_test):
    if not water_test:
        return {
            'headline': 'Testing not completed yet',
            'message': 'Your sample is still in process. Please wait for the laboratory result.',
            'tone': 'warning',
        }

    if water_test.bis_status == 'Safe':
        return {
            'headline': 'Safe water sample',
            'message': 'Your water sample is within acceptable limits and is safe for normal use based on the tested parameters.',
            'tone': 'success',
        }

    if water_test.bis_status == 'Unsafe':
        return {
            'headline': 'Water needs treatment',
            'message': 'Some test values are outside the acceptable range. Please follow the laboratory recommendation before using this water.',
            'tone': 'danger',
        }

    return {
        'headline': 'Result pending review',
        'message': 'The laboratory test is available, but the final water-quality status is still pending.',
        'tone': 'warning',
    }


@role_required('Client')
def client_dashboard(request):
    customer = get_object_or_404(Customer, email=request.user.email)

    samples = Sample.objects.filter(customer=customer).order_by('-id')

    latest_test = WaterTest.objects.filter(
        sample__customer=customer
    ).order_by('-test_date', '-id').first()

    payments = Payment.objects.filter(sample__customer=customer)

    reports = Report.objects.filter(
        sample__customer=customer
    ).select_related(
        'sample',
        'water_test',
        'sample__customer'
    ).order_by('-id')

    history_tests = WaterTest.objects.filter(
        sample__customer=customer,
        sample__sample_status__in=['Completed', 'Report Generated']
    ).select_related(
        'sample'
    ).order_by('test_date', 'id')

    history_labels = []
    history_scores = []
    history_statuses = []

    for test in history_tests:
        history_labels.append(test.test_date.strftime('%d %b %Y'))
        history_scores.append(float(test.water_quality_score or 0))
        history_statuses.append(test.bis_status or 'Pending')

    history_count = len(history_scores)

    latest_score = None
    previous_score = None
    score_change = None

    journey_status = 'First Result'
    journey_message = (
        'Your first completed water-quality result is available. '
        'Complete one more test to begin tracking your water-purity journey.'
    )

    if history_count >= 1:
        latest_score = history_scores[-1]

    if history_count >= 2:
        previous_score = history_scores[-2]
        score_change = round(latest_score - previous_score, 2)

        if score_change > 2:
            journey_status = 'Improving'
            journey_message = (
                f'Your latest water-quality score improved by {score_change} points '
                'compared with the previous completed test.'
            )
        elif score_change < -2:
            journey_status = 'Needs Attention'
            journey_message = (
                f'Your latest water-quality score decreased by {abs(score_change)} points '
                'compared with the previous completed test. Review the latest recommendation '
                'and consider retesting after treatment.'
            )
        else:
            journey_status = 'Stable'
            journey_message = (
                'Your latest water-quality score is broadly stable compared with the previous test.'
            )

    safe_tests_count = history_tests.filter(bis_status='Safe').count()
    unsafe_tests_count = history_tests.filter(bis_status='Unsafe').count()

    context = {
        'customer': customer,
        'total_samples': samples.count(),
        'pending_samples': samples.filter(sample_status='Pending').count(),
        'testing_samples': samples.filter(sample_status='Testing').count(),
        'completed_samples': (
            samples.filter(sample_status='Completed').count()
            + samples.filter(sample_status='Report Generated').count()
        ),
        'latest_test': latest_test,
        'paid_count': payments.filter(payment_status='Paid').count(),
        'pending_count': payments.filter(payment_status='Pending').count(),
        'reports_ready': reports.count(),
        'reports': reports,
        'role': 'Client',

        'history_count': history_count,
        'history_labels': history_labels,
        'history_scores': history_scores,
        'history_statuses': history_statuses,
        'latest_score': latest_score,
        'previous_score': previous_score,
        'score_change': score_change,
        'journey_status': journey_status,
        'journey_message': journey_message,
        'safe_tests_count': safe_tests_count,
        'unsafe_tests_count': unsafe_tests_count,
    }

    return render(request, 'samples/client_dashboard.html', context)


@role_required('Admin', 'Client')
def sample_list(request):
    role = request.user.profile.role

    if role == 'Client':
        customer = get_object_or_404(Customer, email=request.user.email)

        samples = Sample.objects.filter(
            customer=customer
        ).select_related('customer').order_by('-id')
    else:
        samples = Sample.objects.select_related('customer').order_by('-id')

    sample_rows = []

    for sample in samples:
        sample_rows.append({
            'sample': sample,
            'payment': get_payment_for_sample(sample),
            'report': Report.objects.filter(sample=sample).first(),
        })

    return render(request, 'samples/sample_list.html', {
        'sample_rows': sample_rows,
        'role': role,
    })


@role_required('Client')
def sample_create(request):
    customer = get_object_or_404(Customer, email=request.user.email)

    if request.method == 'POST':
        form = SampleForm(request.POST)

        if form.is_valid():
            sample = form.save(commit=False)
            sample.customer = customer
            sample.save()

            return redirect('client_payment_create', sample_id=sample.pk)
    else:
        form = SampleForm(initial={
            'phone_number': customer.phone,
            'email': customer.email,
        })

    return render(request, 'samples/sample_form.html', {
        'form': form,
    })


@role_required('Admin')
def sample_update(request, pk):
    sample = get_object_or_404(Sample, pk=pk)

    if request.method == 'POST':
        form = SampleForm(request.POST, instance=sample)

        if form.is_valid():
            form.save()
            messages.success(request, 'Sample updated successfully.')

            return redirect('sample_detail', pk=sample.pk)
    else:
        form = SampleForm(instance=sample)

    return render(request, 'samples/sample_form.html', {
        'form': form,
        'sample': sample,
        'page_title': 'Edit Sample',
    })


@role_required('Admin')
def sample_delete(request, pk):
    sample = get_object_or_404(Sample, pk=pk)

    if request.method == 'POST':
        sample.delete()
        messages.success(request, 'Sample deleted successfully.')

        return redirect('sample_list')

    return render(request, 'samples/sample_confirm_delete.html', {
        'sample': sample,
    })


@role_required('Admin', 'Client', 'Lab Technician')
def sample_detail(request, pk):
    sample = get_object_or_404(
        Sample.objects.select_related('customer'),
        pk=pk
    )

    role = request.user.profile.role

    if role == 'Client':
        customer = get_object_or_404(Customer, email=request.user.email)

        if sample.customer != customer:
            messages.error(request, 'You are not allowed to view this sample.')

            return redirect('sample_list')

    water_test = WaterTest.objects.filter(
        sample=sample
    ).order_by('-id').first()

    test_result = None

    if water_test:
        test_result = TestResult.objects.filter(
            water_test=water_test
        ).first()

    report = Report.objects.filter(sample=sample).first()
    payment = get_payment_for_sample(sample)

    history = Sample.objects.filter(
        customer=sample.customer
    ).exclude(pk=sample.pk).order_by('-id')[:5]

    parameter_cards = build_parameter_cards(test_result)

    can_generate_report = bool(
        water_test
        and test_result
        and payment
        and payment.payment_status == 'Paid'
    )

    chart_labels = [card['name'] for card in parameter_cards]
    chart_values = [card['value'] for card in parameter_cards]
    client_result_summary = get_client_result_summary(water_test)

    return render(request, 'samples/sample_detail.html', {
        'sample': sample,
        'water_test': water_test,
        'test_result': test_result,
        'report': report,
        'payment': payment,
        'history': history,
        'parameter_cards': parameter_cards,
        'can_generate_report': can_generate_report,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'role': role,
        'client_result_summary': client_result_summary,
    })


@role_required('Lab Technician')
def technician_dashboard(request):
    today = timezone.now().date()

    recent_tests = WaterTest.objects.select_related(
        'sample',
        'sample__customer'
    ).order_by('-id')[:6]

    context = {
        'today_samples': Sample.objects.filter(submission_date=today).count(),
        'pending_samples': Sample.objects.filter(sample_status='Pending').count(),
        'testing_samples': Sample.objects.filter(sample_status='Testing').count(),
        'completed_samples': Sample.objects.filter(sample_status='Completed').count(),
        'report_generated_samples': Sample.objects.filter(
            sample_status='Report Generated'
        ).count(),
        'recent_tests': recent_tests,
        'role': 'Lab Technician',
    }

    return render(request, 'samples/technician_dashboard.html', context)


@role_required('Lab Technician')
def sample_requests(request):
    samples = Sample.objects.select_related('customer').order_by('-id')

    sample_rows = []

    for sample in samples:
        sample_rows.append({
            'sample': sample,
            'payment': get_payment_for_sample(sample),
        })

    return render(request, 'samples/sample_requests.html', {
        'sample_rows': sample_rows,
        'role': 'Lab Technician',
    })


@role_required('Lab Technician')
def accept_sample(request, pk):
    sample = get_object_or_404(Sample, pk=pk)

    sample.sample_status = 'Testing'
    sample.save()

    messages.success(request, 'Sample accepted for laboratory testing.')

    return redirect('sample_requests')


@role_required('Lab Technician')
def process_water_test(request, pk):
    sample = get_object_or_404(Sample, pk=pk)

    water_test = WaterTest.objects.filter(
        sample=sample
    ).order_by('-id').first()

    if not water_test:
        water_test = WaterTest.objects.create(
            sample=sample,
            test_date=timezone.now().date(),
            technician=request.user.username,
            water_quality_score=0,
            bis_status='Pending',
            recommendation='Not yet reviewed',
        )

    sample.sample_status = 'Testing'
    sample.save()

    messages.success(
        request,
        'Water test is ready. You can now enter laboratory parameter values.'
    )

    return redirect('enter_test_results', pk=sample.pk)


@role_required('Lab Technician')
def enter_test_results(request, pk):
    sample = get_object_or_404(Sample, pk=pk)

    water_test = WaterTest.objects.filter(
        sample=sample
    ).order_by('-id').first()

    if not water_test:
        water_test = WaterTest.objects.create(
            sample=sample,
            test_date=timezone.now().date(),
            technician=request.user.username,
            water_quality_score=0,
            bis_status='Pending',
            recommendation='Not yet reviewed',
        )

        sample.sample_status = 'Testing'
        sample.save()

    test_result = TestResult.objects.filter(
        water_test=water_test
    ).first()

    if request.method == 'POST':
        form = TestResultForm(request.POST, instance=test_result)

        if form.is_valid():
            result = form.save(commit=False)
            result.water_test = water_test
            result.save()

            score, bis_status, recommendation = check_bis_and_wqs(result)

            water_test.water_quality_score = score
            water_test.bis_status = bis_status
            water_test.recommendation = recommendation
            water_test.save()

            sample.sample_status = 'Completed'
            sample.save()

            messages.success(
                request,
                f'Test results saved successfully. Score: {score}/100. Status: {bis_status}.'
            )

            return redirect('sample_detail', pk=sample.pk)
    else:
        form = TestResultForm(instance=test_result)

    return render(request, 'samples/technician_result_entry.html', {
        'form': form,
        'sample': sample,
        'water_test': water_test,
        'page_title': 'Enter Test Results',
    })


@role_required('Lab Technician')
def water_test_list(request):
    tests = WaterTest.objects.select_related(
        'sample',
        'sample__customer'
    ).order_by('-id')

    return render(request, 'samples/water_test_list.html', {
        'tests': tests,
    })


@role_required('Lab Technician')
def water_test_create(request):
    if request.method == 'POST':
        form = WaterTestForm(request.POST)

        if form.is_valid():
            water_test = form.save()

            sample = water_test.sample
            sample.sample_status = 'Testing'
            sample.save()

            return redirect('enter_test_results', pk=sample.pk)
    else:
        form = WaterTestForm()

    return render(request, 'samples/water_test_form.html', {
        'form': form,
    })


@role_required('Lab Technician')
def test_result_list(request):
    results = TestResult.objects.select_related(
        'water_test',
        'water_test__sample',
        'water_test__sample__customer'
    ).order_by('-id')

    return render(request, 'samples/test_result_list.html', {
        'results': results,
    })


@role_required('Lab Technician')
def test_result_create(request):
    if request.method == 'POST':
        form = TestResultForm(request.POST)

        if form.is_valid():
            test_result = form.save()

            score, bis_status, recommendation = check_bis_and_wqs(test_result)

            water_test = test_result.water_test
            water_test.water_quality_score = score
            water_test.bis_status = bis_status
            water_test.recommendation = recommendation
            water_test.save()

            sample = water_test.sample
            sample.sample_status = 'Completed'
            sample.save()

            messages.success(
                request,
                f'Test result saved. Score: {score}/100. Status: {bis_status}.'
            )

            return redirect('sample_detail', pk=sample.pk)
    else:
        form = TestResultForm()

    return render(request, 'samples/test_result_form.html', {
        'form': form,
    })


@role_required('Lab Technician')
def test_history(request):
    tests = WaterTest.objects.select_related(
        'sample',
        'sample__customer'
    ).order_by('-id')

    return render(request, 'samples/test_history.html', {
        'tests': tests,
    })