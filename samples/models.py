from django.db import models
from django.utils import timezone
from customers.models import Customer


class Sample(models.Model):
    WATER_SOURCE_CHOICES = [
        ('Borewell', 'Borewell'),
        ('Well', 'Well'),
        ('Tap Water', 'Tap Water'),
        ('River', 'River'),
        ('Lake', 'Lake'),
        ('Tank', 'Tank'),
    ]

    SEASON_CHOICES = [
        ('Summer', 'Summer'),
        ('Monsoon', 'Monsoon'),
        ('Winter', 'Winter'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Testing', 'Testing'),
        ('Completed', 'Completed'),
        ('Report Generated', 'Report Generated'),
    ]

    COLLECTION_METHOD_CHOICES = [
        ('Self-collected', 'Self-collected'),
        ('Collected by Lab Technician', 'Collected by Lab Technician'),
    ]

    SAMPLE_TYPE_CHOICES = [
        ('Drinking Water', 'Drinking Water'),
        ('Groundwater', 'Groundwater'),
        ('Surface Water', 'Surface Water'),
        ('Industrial Water', 'Industrial Water'),
    ]

    PURPOSE_CHOICES = [
        ('Drinking', 'Drinking'),
        ('Domestic', 'Domestic'),
        ('Commercial', 'Commercial'),
        ('Industrial', 'Industrial'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    sample_code = models.CharField(max_length=20, unique=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    collection_date = models.DateField(blank=True, null=True)
    submission_date = models.DateField(default=timezone.now, blank=True, null=True)
    water_source = models.CharField(max_length=50, choices=WATER_SOURCE_CHOICES)
    sample_location = models.TextField(blank=True, null=True)
    district_city = models.CharField(max_length=100, blank=True, null=True)
    sample_type = models.CharField(max_length=50, choices=SAMPLE_TYPE_CHOICES, blank=True, null=True)
    purpose_of_testing = models.CharField(max_length=50, choices=PURPOSE_CHOICES, blank=True, null=True)
    collection_method = models.CharField(max_length=50, choices=COLLECTION_METHOD_CHOICES, blank=True, null=True)
    sample_volume = models.CharField(max_length=50, blank=True, null=True)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES)
    sample_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    remarks = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.sample_code:
            last_sample = Sample.objects.order_by('-id').first()
            next_id = 1 if not last_sample else last_sample.id + 1
            self.sample_code = f"HVS{next_id:03d}"

        if self.customer:
            if not self.phone_number:
                self.phone_number = self.customer.phone
            if not self.email:
                self.email = self.customer.email

        super().save(*args, **kwargs)

    def __str__(self):
        return self.sample_code


class WaterTest(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    test_date = models.DateField(default=timezone.now)
    technician = models.CharField(max_length=100, default='Lab Technician')
    water_quality_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    bis_status = models.CharField(max_length=50, default='Pending')
    recommendation = models.TextField(default='Not yet reviewed')

    def __str__(self):
        return f"Water Test - {self.sample.sample_code}"


class TestResult(models.Model):
    water_test = models.OneToOneField(WaterTest, on_delete=models.CASCADE)
    ph = models.FloatField()
    tds = models.FloatField()
    turbidity = models.FloatField()
    hardness = models.FloatField()
    fluoride = models.FloatField()
    iron = models.FloatField()
    nitrate = models.FloatField()
    chloride = models.FloatField()
    sulphate = models.FloatField(default=0)
    alkalinity = models.FloatField(default=0)

    def __str__(self):
        return f"Results - {self.water_test.sample.sample_code}"