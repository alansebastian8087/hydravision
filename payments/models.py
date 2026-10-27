from django.db import models
from samples.models import Sample


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Cash', 'Cash'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
    ]

    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=300.00)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    payment_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Payment - {self.sample.sample_code}"