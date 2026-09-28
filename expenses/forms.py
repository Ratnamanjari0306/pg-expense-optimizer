from django import forms
from django.utils import timezone
from .models import Expense,MonthlyBudget


class ExpenseForm(forms.ModelForm):

    class Meta:
        model = Expense

        fields = [
            'date',
            'category',
            'description',
            'amount',
            'payment_method',
            'recurring',
        ]

        widgets = {

            'date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),

            'category': forms.TextInput(
                attrs={
                    'placeholder': 'Example: Food, Rent, Transport'
                }
            ),

            'description': forms.TextInput(
                attrs={
                    'placeholder': 'Example: Monthly PG rent'
                }
            ),

            'amount': forms.NumberInput(
                attrs={
                    'placeholder': 'Enter amount',
                    'step': '0.01',
                    'min': '0'
                }
            ),

            'payment_method': forms.TextInput(
                attrs={
                    'placeholder': 'Example: UPI, Cash, Card'
                }
            ),

            'recurring': forms.CheckboxInput(
                attrs={
                    'class': 'recurring-checkbox'
                }
            ),
        }

class MonthlyBudgetForm(forms.ModelForm):

    month = forms.CharField(
        label="Month",
        widget=forms.TextInput(
            attrs={
                "type": "month"
            }
        )
    )

    class Meta:
        model = MonthlyBudget
        fields = ["month", "amount"]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "placeholder": "Example: 15000",
                    "step": "0.01",
                    "min": "0"
                }
            )
        }

    def clean_month(self):
        month = self.cleaned_data["month"]

        try:
            year, month_number = month.split("-")
            return timezone.datetime(
                int(year),
                int(month_number),
                1
            ).date()
        except (ValueError, TypeError):
            raise forms.ValidationError(
                "Please select a valid month."
            )