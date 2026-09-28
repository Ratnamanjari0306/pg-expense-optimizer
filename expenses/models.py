from django.db import models


class Expense(models.Model):

    CATEGORY_CHOICES = [
        ('Rent', 'Rent'),
        ('Food', 'Food'),
        ('Groceries', 'Groceries'),
        ('Transport', 'Transport'),
        ('Electricity', 'Electricity'),
        ('Mobile/Internet', 'Mobile/Internet'),
        ('Personal', 'Personal'),
        ('Entertainment', 'Entertainment'),
        ('Other', 'Other'),
    ]

    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('UPI', 'UPI'),
        ('Card', 'Card'),
        ('Other', 'Other'),
    ]

    date = models.DateField()
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES
    )
    recurring = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - ₹{self.amount}"

class MonthlyBudget(models.Model):
    month = models.DateField(unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.month.strftime('%B %Y')} - ₹{self.amount}"