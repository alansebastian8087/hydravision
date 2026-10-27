import socket

from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.contrib import messages

from samples.models import WaterTest, TestResult
from customers.models import Customer
from payments.models import Payment

from .models import Report
from .utils import generate_qr_code, generate_pdf_report
from accounts.decorators import role_required


def build_qr_pdf_url(request, report):
    if not report.pdf_file:
        return None

    pdf_url = request.build_absolute_uri(report.pdf_file.url)
    host = request.get_host()

    if host.startswith('127.0.0.1') or host.startswith('localhost'):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())

            if local_ip and not local_ip.startswith('127.'):
                pdf_url = pdf_url.replace(
                    host,
                    f'{local_ip}:8000'
                )
        except Exception:
            pass

    return pdf_url


def get_payment(sample):
    return Payment.objects.filter(sample=sample).order_by('-id').first()


def build_chart_data(test_result):
    if not test_result:
        return [], []

    labels = [
        'pH',
        'TDS',
        'Turbidity',
        'Hardness',
        'Fluoride',
        'Iron',
        'Nitrate',
        'Chloride',
        'Sulphate',
        'Alkalinity',
    ]

    values = [
        test_result.ph,
        test_result.tds,
        test_result.turbidity,
        test_result.hardness,
        test_result.fluoride,
        test_result.iron,
        test_result.nitrate,
        test_result.chloride,
        test_result.sulphate,
        test_result.alkalinity,
    ]

    return labels, values


@role_required('Admin', 'Lab Technician', 'Client')
def report_list(request):
    role = request.user.profile.role

    if role == 'Client':
        customer = get_object_or_404(Customer, email=request.user.email)

        reports = Report.objects.filter(
            sample__customer=customer
        ).select_related(
            'sample',
            'water_test',
            'sample__customer'
        ).order_by('-id')
    else:
        reports = Report.objects.select_related(
            'sample',
            'water_test',
            'sample__customer'
        ).order_by('-id')

    report_rows = []

    for report in reports:
        report_rows.append({
            'report': report,
            'payment': get_payment(report.sample),
        })

    return render(request, 'reports/report_list.html', {
        'report_rows': report_rows,
        'role': role,
    })


@role_required('Admin', 'Lab Technician')
def generate_report(request, water_test_id):
    water_test = get_object_or_404(
        WaterTest.objects.select_related('sample', 'sample__customer'),
        pk=water_test_id
    )

    test_result = TestResult.objects.filter(
        water_test=water_test
    ).first()

    if not test_result:
        messages.error(request, 'Test results are not available yet.')
        return redirect('sample_detail', pk=water_test.sample.pk)

    payment = get_payment(water_test.sample)

    if not payment or payment.payment_status != 'Paid':
        messages.error(
            request,
            'Report generation is allowed only after payment approval.'
        )
        return redirect('sample_detail', pk=water_test.sample.pk)

    report, created = Report.objects.get_or_create(
        sample=water_test.sample,
        defaults={
            'water_test': water_test,
        }
    )

    report.sample = water_test.sample
    report.water_test = water_test
    report.save()

    # Step 1: Save a PDF first, so report.pdf_file.url exists.
    initial_pdf_buffer = generate_pdf_report(report, request=request)

    report.pdf_file.save(
        f'{water_test.sample.sample_code}_report.pdf',
        ContentFile(initial_pdf_buffer.getvalue()),
        save=False
    )
    report.save()

    # Step 2: Build QR code containing the direct PDF URL.
    try:
        pdf_url = build_qr_pdf_url(request, report)

        if not pdf_url:
            raise ValueError('Could not create a PDF URL for the QR code.')

        qr_buffer = generate_qr_code(report, pdf_url)

        report.qr_code.save(
            f'{water_test.sample.sample_code}_qr.png',
            ContentFile(qr_buffer.getvalue()),
            save=False
        )
        report.save()

    except Exception as error:
        messages.error(
            request,
            f'QR code generation failed: {error}'
        )
        return redirect('sample_detail', pk=water_test.sample.pk)

    # Step 3: Rebuild the PDF after the QR image exists.
    # generate_pdf_report() can now embed report.qr_code inside the PDF.
    final_pdf_buffer = generate_pdf_report(report, request=request)

    report.pdf_file.save(
        f'{water_test.sample.sample_code}_report.pdf',
        ContentFile(final_pdf_buffer.getvalue()),
        save=False
    )
    report.save()

    sample = water_test.sample
    sample.sample_status = 'Report Generated'
    sample.save()

    messages.success(
        request,
        'Report generated successfully. The QR code now opens the PDF report.'
    )

    return redirect('report_detail', pk=report.pk)


@role_required('Admin', 'Lab Technician', 'Client')
def report_detail(request, pk):
    report = get_object_or_404(
        Report.objects.select_related(
            'sample',
            'water_test',
            'sample__customer'
        ),
        pk=pk
    )

    role = request.user.profile.role

    if role == 'Client':
        customer = get_object_or_404(
            Customer,
            email=request.user.email
        )

        if report.sample.customer != customer:
            return render(request, 'accounts/access_denied.html')

    test_result = TestResult.objects.filter(
        water_test=report.water_test
    ).first()

    payment = get_payment(report.sample)
    chart_labels, chart_values = build_chart_data(test_result)

    parameter_rows = []

    if test_result:
        parameter_rows = [
            ('pH', test_result.ph, '6.5 - 8.5'),
            ('TDS', test_result.tds, '≤ 500 mg/L'),
            ('Turbidity', test_result.turbidity, '≤ 1 NTU'),
            ('Hardness', test_result.hardness, '≤ 200 mg/L'),
            ('Fluoride', test_result.fluoride, '≤ 1.0 mg/L'),
            ('Iron', test_result.iron, '≤ 0.3 mg/L'),
            ('Nitrate', test_result.nitrate, '≤ 45 mg/L'),
            ('Chloride', test_result.chloride, '≤ 250 mg/L'),
            ('Sulphate', test_result.sulphate, '≤ 200 mg/L'),
            ('Alkalinity', test_result.alkalinity, '≤ 200 mg/L'),
        ]

    return render(request, 'reports/report_detail.html', {
        'report': report,
        'role': role,
        'payment': payment,
        'test_result': test_result,
        'parameter_rows': parameter_rows,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    })