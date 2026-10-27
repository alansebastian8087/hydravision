from django import forms
from .models import WaterTest, TestResult

class WaterTestForm(forms.ModelForm):
    class Meta:
        model = WaterTest
        fields = [
            'sample',
            'test_date',
            'technician',
            'water_quality_score',
            'bis_status',
            'recommendation',
        ]
        widgets = {
            'test_date': forms.DateInput(attrs={'type': 'date'}),
        }

class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = [
            'water_test',
            'ph',
            'tds',
            'turbidity',
            'hardness',
            'fluoride',
            'iron',
            'nitrate',
            'chloride',
        ]