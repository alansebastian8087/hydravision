from django.db import models
from samples.models import Sample, WaterTest


class Report(models.Model):
    sample = models.OneToOneField(
        Sample,
        on_delete=models.CASCADE,
        related_name='report',
        null=True,
        blank=True
    )
    water_test = models.ForeignKey(WaterTest, on_delete=models.CASCADE)
    generated_on = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='reports/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='reports/qr_codes/', blank=True, null=True)

    def __str__(self):
        return f"Report for {self.sample.sample_code if self.sample else 'No Sample'}"