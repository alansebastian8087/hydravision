from django import forms
from .models import Sample, WaterTest, TestResult


class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        exclude = ['customer', 'sample_code', 'sample_status']
        widgets = {
            'collection_date': forms.DateInput(attrs={'type': 'date'}),
            'submission_date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3}),
            'sample_location': forms.Textarea(attrs={'rows': 3}),
        }


class WaterTestForm(forms.ModelForm):
    class Meta:
        model = WaterTest
        fields = [
            'sample',
            'test_date',
            'technician',
        ]
        widgets = {
            'test_date': forms.DateInput(attrs={'type': 'date'}),
            'technician': forms.TextInput(
                attrs={'placeholder': 'Lab Technician'}
            ),
        }


class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = [
            'ph',
            'tds',
            'turbidity',
            'hardness',
            'fluoride',
            'iron',
            'nitrate',
            'chloride',
            'sulphate',
            'alkalinity',
        ]

        labels = {
            'ph': 'pH',
            'tds': 'TDS (mg/L)',
            'turbidity': 'Turbidity (NTU)',
            'hardness': 'Hardness (mg/L)',
            'fluoride': 'Fluoride (mg/L)',
            'iron': 'Iron (mg/L)',
            'nitrate': 'Nitrate (mg/L)',
            'chloride': 'Chloride (mg/L)',
            'sulphate': 'Sulphate (mg/L)',
            'alkalinity': 'Alkalinity (mg/L as CaCO₃)',
        }

        widgets = {
            'ph': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 7.2',
                'autocomplete': 'off',
            }),
            'tds': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 300',
                'autocomplete': 'off',
            }),
            'turbidity': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 0.5',
                'autocomplete': 'off',
            }),
            'hardness': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 150',
                'autocomplete': 'off',
            }),
            'fluoride': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 0.7',
                'autocomplete': 'off',
            }),
            'iron': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 0.1',
                'autocomplete': 'off',
            }),
            'nitrate': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 20',
                'autocomplete': 'off',
            }),
            'chloride': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 150',
                'autocomplete': 'off',
            }),
            'sulphate': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 150',
                'autocomplete': 'off',
            }),
            'alkalinity': forms.TextInput(attrs={
                'inputmode': 'decimal',
                'placeholder': 'Example: 120',
                'autocomplete': 'off',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        numeric_fields = [
            'ph',
            'tds',
            'turbidity',
            'hardness',
            'fluoride',
            'iron',
            'nitrate',
            'chloride',
            'sulphate',
            'alkalinity',
        ]

        for field_name in numeric_fields:
            value = cleaned_data.get(field_name)

            if value is not None and value < 0:
                self.add_error(
                    field_name,
                    'Please enter a value greater than or equal to 0.'
                )

        return cleaned_data