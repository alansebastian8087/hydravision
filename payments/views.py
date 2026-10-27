from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages

from .models import Payment
from .forms import PaymentForm, ClientPaymentForm, AdminPaymentApprovalForm
from accounts.decorators import role_required
from customers.models import Customer
from reports.models import Report
from samples.models import Sample


FIXED_PAYMENT_AMOUNT = 300


@role_required('Admin', 'Client')
def payment_list(request):
    role = request.user.profile.role

    if role == 'Client':
        customer = get_object_or_404(Customer, email=request.user.email)
        payments = Payment.objects.select_related('sample', 'sample__customer').filter(
            sample__customer=customer
        ).order_by('-id')
    else:
        payments = Payment.objects.select_related('sample', 'sample__customer').all().order_by('-id')

    payment_rows = []
    for payment in payments:
        payment_rows.append({
            "payment": payment,
            "report": Report.objects.filter(sample=payment.sample).first(),
        })

    summary = {
        "total": payments.count(),
        "paid": payments.filter(payment_status='Paid').count(),
        "pending": payments.filter(payment_status='Pending').count(),
    }

    return render(request, 'payments/payment_list.html', {
        'payment_rows': payment_rows,
        'summary': summary,
        'role': role,
        'fixed_amount': FIXED_PAYMENT_AMOUNT,
    })


@role_required('Client')
def client_payment_create(request, sample_id):
    customer = get_object_or_404(Customer, email=request.user.email)
    sample = get_object_or_404(Sample, pk=sample_id, customer=customer)

    existing_payment = Payment.objects.filter(sample=sample).first()
    if existing_payment:
        messages.info(request, 'Payment already exists for this sample.')
        return redirect('sample_detail', pk=sample.pk)

    if request.method == 'POST':
        form = ClientPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.sample = sample
            payment.amount = FIXED_PAYMENT_AMOUNT
            payment.payment_status = 'Pending'
            payment.payment_date = timezone.now().date()
            payment.save()
            messages.success(request, 'Demo payment submitted successfully.')
            return redirect('sample_detail', pk=sample.pk)
    else:
        form = ClientPaymentForm()

    return render(request, 'payments/client_payment_form.html', {
        'form': form,
        'sample': sample,
        'fixed_amount': FIXED_PAYMENT_AMOUNT,
        'page_title': 'Demo Payment',
    })


@role_required('Admin')
def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            if not payment.amount:
                payment.amount = FIXED_PAYMENT_AMOUNT
            if payment.payment_status == 'Paid' and not payment.payment_date:
                payment.payment_date = timezone.now().date()
            payment.save()
            return redirect('payment_list')
    else:
        form = PaymentForm(initial={'amount': FIXED_PAYMENT_AMOUNT})

    return render(request, 'payments/payment_form.html', {
        'form': form,
        'page_title': 'Add Payment',
        'fixed_amount': FIXED_PAYMENT_AMOUNT,
    })


@role_required('Admin')
def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)

    if request.method == 'POST':
        form = AdminPaymentApprovalForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.amount = FIXED_PAYMENT_AMOUNT
            payment.payment_status = 'Paid'
            if not payment.payment_date:
                payment.payment_date = timezone.now().date()
            payment.save()
            messages.success(request, 'Payment approved successfully.')
            return redirect('payment_list')
    else:
        if not payment.amount:
            payment.amount = FIXED_PAYMENT_AMOUNT
        form = AdminPaymentApprovalForm(instance=payment)

    return render(request, 'payments/payment_approval_form.html', {
        'form': form,
        'payment': payment,
        'page_title': 'Approve Payment',
        'fixed_amount': FIXED_PAYMENT_AMOUNT,
    })


@role_required('Admin')
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        return redirect('payment_list')
    return render(request, 'payments/payment_confirm_delete.html', {'payment': payment})