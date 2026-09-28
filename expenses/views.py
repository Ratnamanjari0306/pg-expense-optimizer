from django.shortcuts import render, redirect
from django.db.models import Sum
from django.utils import timezone
from .models import Expense, MonthlyBudget
from .forms import ExpenseForm, MonthlyBudgetForm
from openai import OpenAI
from calendar import month_name
import os

# ==========================================
# DASHBOARD
# ==========================================

def dashboard(request):

    expenses = Expense.objects.all().order_by('-date', '-created_at')

    # ==========================================
    # TOTAL EXPENSE
    # ==========================================

    total_expense = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # ==========================================
    # TOTAL TRANSACTIONS
    # ==========================================

    total_transactions = expenses.count()

    # ==========================================
    # CATEGORY TOTALS
    # ==========================================

    category_totals = (
        expenses
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # ==========================================
    # TOP CATEGORY
    # ==========================================

    top_category = category_totals.first()

    if top_category:
        top_spending_category = top_category['category']
        top_category_amount = top_category['total']
    else:
        top_spending_category = "No expenses yet"
        top_category_amount = 0

    # ==========================================
    # AVERAGE EXPENSE
    # ==========================================

    if total_transactions > 0:
        average_expense = total_expense / total_transactions
    else:
        average_expense = 0

    # ==========================================
    # HIGHEST EXPENSE
    # ==========================================

    highest_expense = expenses.order_by('-amount').first()

    # ==========================================
    # LOWEST EXPENSE
    # ==========================================

    lowest_expense = expenses.order_by('amount').first()

    # ==========================================
    # TOP CATEGORY PERCENTAGE
    # ==========================================

    if total_expense > 0 and top_category:
        top_category_percentage = (
            top_category_amount / total_expense
        ) * 100
    else:
        top_category_percentage = 0

    # ==========================================
    # SPENDING INSIGHT
    # ==========================================

    if top_category:
        spending_insight = (
            f"{top_spending_category} is your highest spending "
            f"category, accounting for "
            f"{top_category_percentage:.1f}% of your total expenses."
        )
    else:
        spending_insight = (
            "Start adding expenses to see your spending insights."
        )

    # ==========================================
    # CURRENT MONTH
    # ==========================================

    today = timezone.now().date()

    current_month = today.replace(day=1)

    # ==========================================
    # CURRENT MONTH EXPENSES
    # ==========================================

    monthly_expenses = expenses.filter(
        date__year=today.year,
        date__month=today.month
    )

    monthly_spent = monthly_expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # ==========================================
    # CURRENT MONTH CATEGORY TOTALS
    # ==========================================

    monthly_category_totals = (
        monthly_expenses
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # ==========================================
    # MONTHLY BUDGET
    # ==========================================

    monthly_budget = MonthlyBudget.objects.filter(
        month__month=today.month,
        month__year=today.year
    ).first()

    if monthly_budget:

        budget_amount = monthly_budget.amount

        budget_remaining = budget_amount - monthly_spent

        if budget_amount > 0:
            budget_percentage = (
                monthly_spent / budget_amount
            ) * 100
        else:
            budget_percentage = 0

        # ======================================
        # BUDGET ALERT
        # ======================================

        if budget_percentage >= 100:

            budget_status = "Budget Exceeded"
            budget_status_class = "danger"

            budget_alert = (
                f"You have exceeded your monthly budget by "
                f"₹{abs(budget_remaining):.2f}."
            )

        elif budget_percentage >= 90:

            budget_status = "Critical"
            budget_status_class = "danger"

            budget_alert = (
                f"You have used {budget_percentage:.1f}% of your "
                f"monthly budget. Only ₹{budget_remaining:.2f} remains."
            )

        elif budget_percentage >= 70:

            budget_status = "Approaching Limit"
            budget_status_class = "warning"

            budget_alert = (
                f"You have used {budget_percentage:.1f}% of your "
                f"monthly budget. Spend carefully for the rest of the month."
            )

        else:

            budget_status = "Within Budget"
            budget_status_class = "success"

            budget_alert = (
                f"You have used {budget_percentage:.1f}% of your "
                f"monthly budget. You're currently within your spending limit."
            )

    else:

        # ======================================
        # NO BUDGET SET
        # ======================================

        budget_amount = 0
        budget_remaining = 0
        budget_percentage = 0

        budget_status = "No Budget Set"
        budget_status_class = "neutral"

        budget_alert = (
            "Set a monthly budget to start receiving budget alerts."
        )

    # ==========================================
    # DASHBOARD
    # ==========================================

    return render(
        request,
        'dashboard.html',
        {
            'expenses': expenses,

            'total_expense': total_expense,
            'total_transactions': total_transactions,

            'top_spending_category': top_spending_category,
            'category_totals': category_totals,

            'average_expense': average_expense,
            'highest_expense': highest_expense,
            'lowest_expense': lowest_expense,

            'top_category_percentage': top_category_percentage,
            'spending_insight': spending_insight,

            # CURRENT MONTH
            'monthly_expenses': monthly_expenses,
            'monthly_spent': monthly_spent,
            'monthly_category_totals': monthly_category_totals,

            # BUDGET DATA
            'monthly_budget': monthly_budget,
            'budget_amount': budget_amount,
            'budget_remaining': budget_remaining,
            'budget_percentage': budget_percentage,

            # BUDGET ALERT
            'budget_status': budget_status,
            'budget_status_class': budget_status_class,
            'budget_alert': budget_alert,
        }
    )


# ==========================================
# ADD EXPENSE
# ==========================================

def add_expense(request):

    if request.method == 'POST':

        form = ExpenseForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('dashboard')

    else:

        form = ExpenseForm()

    return render(
        request,
        'add_expense.html',
        {'form': form}
    )


# ==========================================
# SET BUDGET
# ==========================================

def set_budget(request):

    today = timezone.now().date()
    current_month = today.replace(day=1)

    existing_budget = MonthlyBudget.objects.filter(
        month=current_month
    ).first()

    if request.method == 'POST':

        form = MonthlyBudgetForm(request.POST)

        if form.is_valid():

            budget = form.save(commit=False)

            budget.month = budget.month.replace(day=1)

            existing = MonthlyBudget.objects.filter(
                month=budget.month
            ).first()

            if existing:

                existing.amount = budget.amount
                existing.save()

            else:

                budget.save()

            return redirect('dashboard')

    else:

        if existing_budget:

            form = MonthlyBudgetForm(
                initial={
                    'month': existing_budget.month.strftime('%Y-%m')
                }
            )

        else:

            form = MonthlyBudgetForm(
                initial={
                    'month': current_month.strftime('%Y-%m')
                }
            )

    return render(
        request,
        'set_budget.html',
        {
            'form': form
        }
    )


# ==========================================
# MONTHLY BUDGET PAGE
# ==========================================

def monthly_budget(request):

    today = timezone.now().date()

    # ==========================================
    # SELECT MONTH
    # ==========================================

    selected_month = request.GET.get('month')

    if selected_month:

        try:
            selected_year, selected_month_number = map(
                int,
                selected_month.split('-')
            )

        except (ValueError, TypeError):

            selected_year = today.year
            selected_month_number = today.month

    else:

        selected_year = today.year
        selected_month_number = today.month

    selected_month_value = (
        f"{selected_year}-{selected_month_number:02d}"
    )

    selected_month_label = (
        f"{month_name[selected_month_number]} "
        f"{selected_year}"
    )

    # ==========================================
    # GET SELECTED MONTH'S BUDGET
    # ==========================================

    budget = MonthlyBudget.objects.filter(
        month__year=selected_year,
        month__month=selected_month_number
    ).first()

    # ==========================================
    # GET SELECTED MONTH'S EXPENSES
    # ==========================================

    spent = Expense.objects.filter(
        date__year=selected_year,
        date__month=selected_month_number
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # ==========================================
    # BUDGET AMOUNT
    # ==========================================

    budget_amount = budget.amount if budget else 0

    # ==========================================
    # REMAINING BUDGET
    # ==========================================

    remaining = budget_amount - spent

    # ==========================================
    # BUDGET UTILIZATION
    # ==========================================

    if budget_amount > 0:

        percentage_used = (
            spent / budget_amount
        ) * 100

    else:

        percentage_used = 0

    # ==========================================
    # BUDGET STATUS
    # ==========================================

    if not budget:

        budget_status = "No Budget Set"
        budget_status_class = "neutral"

        budget_message = (
            f"No budget has been set for "
            f"{selected_month_label}."
        )

    elif percentage_used >= 100:

        budget_status = "Budget Exceeded"
        budget_status_class = "danger"

        budget_message = (
            f"You have exceeded your "
            f"{selected_month_label} budget by "
            f"₹{abs(remaining):.2f}."
        )

    elif percentage_used >= 90:

        budget_status = "Critical"
        budget_status_class = "danger"

        budget_message = (
            f"You have used {percentage_used:.1f}% of your "
            f"{selected_month_label} budget. "
            f"Only ₹{remaining:.2f} remains."
        )

    elif percentage_used >= 70:

        budget_status = "Approaching Limit"
        budget_status_class = "warning"

        budget_message = (
            f"You have used {percentage_used:.1f}% of your "
            f"{selected_month_label} budget. "
            f"Consider reducing non-essential spending."
        )

    else:

        budget_status = "Within Budget"
        budget_status_class = "success"

        budget_message = (
            f"You have used {percentage_used:.1f}% of your "
            f"{selected_month_label} budget. "
            f"You're currently within your spending limit."
        )

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        'budget': budget,
        'budget_amount': budget_amount,
        'spent': spent,
        'remaining': remaining,
        'percentage_used': percentage_used,

        'budget_status': budget_status,
        'budget_status_class': budget_status_class,
        'budget_message': budget_message,

        'current_month': selected_month_label,

        'selected_month': selected_month_value,
        'selected_month_label': selected_month_label,
    }

    return render(
        request,
        'monthly_budget.html',
        context
    )

# ==========================================
# AI SPENDING OPTIMIZER
# ==========================================

def optimize_spending(request):

    if request.method == "POST":

        # ==========================================
        # SELECTED MONTH
        # ==========================================

        selected_month = request.POST.get("month")

        today = timezone.now().date()

        if selected_month:

            try:
                selected_year, selected_month_number = map(
                    int,
                    selected_month.split("-")
                )

            except (ValueError, TypeError):

                selected_year = today.year
                selected_month_number = today.month

        else:

            selected_year = today.year
            selected_month_number = today.month

        selected_month_label = (
            f"{month_name[selected_month_number]} "
            f"{selected_year}"
        )

        # ==========================================
        # SELECTED MONTH EXPENSES
        # ==========================================

        monthly_expenses = Expense.objects.filter(
            date__year=selected_year,
            date__month=selected_month_number
        )

        # ==========================================
        # TOTAL SPENDING
        # ==========================================

        total_spent = monthly_expenses.aggregate(
            total=Sum("amount")
        )["total"] or 0

        # ==========================================
        # CATEGORY-WISE SPENDING
        # ==========================================

        category_totals = list(
            monthly_expenses
            .values("category")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        # ==========================================
        # MONTHLY BUDGET
        # ==========================================

        monthly_budget = MonthlyBudget.objects.filter(
            month__year=selected_year,
            month__month=selected_month_number
        ).first()

        if monthly_budget:

            budget_amount = monthly_budget.amount

            remaining_budget = (
                budget_amount - total_spent
            )

            if budget_amount > 0:

                budget_percentage = (
                    total_spent / budget_amount
                ) * 100

            else:

                budget_percentage = 0

        else:

            budget_amount = 0
            remaining_budget = 0
            budget_percentage = 0

        # ==========================================
        # HIGHEST SPENDING CATEGORY
        # ==========================================

        if category_totals:

            highest_category = category_totals[0]["category"]
            highest_category_amount = category_totals[0]["total"]

        else:

            highest_category = "None"
            highest_category_amount = 0

        # ==========================================
        # CATEGORY INFORMATION FOR AI
        # ==========================================

        category_text = "\n".join(
            [
                f"{item['category']}: ₹{item['total']}"
                for item in category_totals
            ]
        )

        # ==========================================
        # AI PROMPT
        # ==========================================

        prompt = f"""
You are an AI spending optimization assistant for a student living in a PG.

Analyze ONLY the financial data provided below.

Month being analyzed: {selected_month_label}

Monthly budget: ₹{budget_amount}
Total spent: ₹{total_spent}
Remaining budget: ₹{remaining_budget}
Budget used: {round(float(budget_percentage), 2)}%

Category-wise spending:
{category_text}

Highest spending category:
{highest_category} - ₹{highest_category_amount}

Your job is to identify spending patterns and provide practical recommendations.

Follow these rules:

1. Start with a short assessment of the student's current spending.
2. Identify the category that needs the most attention and explain why using the provided numbers.
3. Give 2-3 specific and realistic ways to reduce spending.
4. Suggest a realistic savings target for the remaining budget.
5. If spending is already within the budget, acknowledge that.
6. If the budget has been exceeded, clearly mention it and suggest immediate corrective actions.
7. Do not invent expenses, prices, income, or personal information.
8. Do not give generic financial advice unrelated to the provided data.
9. Keep the response concise and easy for a student to understand.

Use this format:

📊 Spending Assessment:
[short assessment]

🎯 Main Area to Improve:
[category + explanation]

💡 Recommendations:
• [recommendation]
• [recommendation]
• [recommendation]

💰 Suggested Savings Target:
[amount and short explanation]
"""

        # ==========================================
        # OPENROUTER
        # ==========================================

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )

        try:

            response = client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            ai_recommendation = (
                response.choices[0].message.content
            )

        except Exception as e:

            print("AI ERROR:", e)

            ai_recommendation = (
                "AI recommendations are temporarily unavailable. "
                "Please try again later."
            )

        # ==========================================
        # SEND DATA TO TEMPLATE
        # ==========================================

        context = {

            "total_spent": total_spent,

            "budget_amount": budget_amount,

            "remaining_budget": remaining_budget,

            "category_totals": category_totals,

            "ai_recommendation": ai_recommendation,

            "selected_month": (
                f"{selected_year}-{selected_month_number:02d}"
            ),

            "selected_month_label": selected_month_label,
        }

        return render(
            request,
            "optimizer.html",
            context
        )

    return redirect("dashboard")

# spending_analytics
def spending_analytics(request):

    expenses = Expense.objects.all()

    # Total spending
    total_spent = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Average expense
    total_transactions = expenses.count()

    if total_transactions > 0:
        average_expense = total_spent / total_transactions
    else:
        average_expense = 0

    # Category-wise spending
    category_totals = list(
        expenses.values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # Highest spending category
    if category_totals:
        highest_category = category_totals[0]['category']
        highest_category_amount = category_totals[0]['total']
    else:
        highest_category = "No data"
        highest_category_amount = 0

    # Payment method breakdown
    payment_totals = list(
        expenses.values('payment_method')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    # Monthly spending trend
    monthly_totals = list(
        expenses.values(
            'date__year',
            'date__month'
        )
        .annotate(total=Sum('amount'))
        .order_by(
            'date__year',
            'date__month'
        )
    )

    # Create readable month labels
    for item in monthly_totals:
        item['month_label'] = (
            f"{month_name[item['date__month']]} "
            f"{item['date__year']}"
    )

    # Month-over-month spending change
    mom_change = None
    mom_change_label = "Not enough data"

    if len(monthly_totals) >= 2:

        previous_month_total = monthly_totals[-2]['total']
        current_month_total = monthly_totals[-1]['total']

        if previous_month_total > 0:

            mom_change = (
                (current_month_total - previous_month_total)
                / previous_month_total
            ) * 100

            if mom_change > 0:
                mom_change_label = "Spending increased"

            elif mom_change < 0:
                mom_change_label = "Spending decreased"

            else:
                mom_change_label = "No change"

    # Highest and lowest spending month
    highest_spending_month = None
    lowest_spending_month = None

    if monthly_totals:

        highest_spending_month = max(
            monthly_totals,
            key=lambda x: x['total']
        )

        lowest_spending_month = min(
            monthly_totals,
            key=lambda x: x['total']
        )

          # SELECTED MONTH BUDGET VS ACTUAL

    selected_budget = None
    selected_actual = 0
    selected_remaining = 0
    selected_status = None
    selected_status_class = "neutral"
    selected_utilization = 0

    selected_month = request.GET.get('month')

    selected_month_label = None

    if selected_month:

        try:

            selected_year, selected_month_number = map(
                int,
                selected_month.split('-')
            )

            selected_month_label = (
                f"{month_name[selected_month_number]} {selected_year}"
            )

            selected_budget = MonthlyBudget.objects.filter(
                month__year=selected_year,
                month__month=selected_month_number
            ).first()

            selected_actual = Expense.objects.filter(
                date__year=selected_year,
                date__month=selected_month_number
            ).aggregate(
                total=Sum('amount')
            )['total'] or 0

            if selected_budget:

                selected_remaining = (
                    selected_budget.amount - selected_actual
                )

                if selected_budget.amount > 0:
                    selected_utilization = (
                        selected_actual / selected_budget.amount
                    ) * 100

                if selected_utilization >= 100:
                    selected_status = "Over Budget"
                    selected_status_class = "danger"

                elif selected_utilization >= 90:
                    selected_status = "Critical"
                    selected_status_class = "danger"

                elif selected_utilization >= 70:
                    selected_status = "Approaching Limit"
                    selected_status_class = "warning"

                else:
                    selected_status = "Within Budget"
                    selected_status_class = "success"


        except (ValueError, TypeError):

            selected_month = None

        # AVAILABLE MONTHS

    available_months = []
 
    for item in monthly_totals:
        year = item['date__year']
        month = item['date__month']

        available_months.append({
            'value': f"{year}-{month:02d}",
            'label': f"{month_name[month]} {year}",
        })

    # Recurring vs non-recurring
    recurring_expenses = expenses.filter(
        recurring=True
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    non_recurring_expenses = expenses.filter(
        recurring=False
    ).aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Context
    context = {

        'total_spent': total_spent,
        'total_transactions': total_transactions,
        'average_expense': average_expense,

        'category_totals': category_totals,
        'highest_category': highest_category,
        'highest_category_amount': highest_category_amount,

        'payment_totals': payment_totals,

        'recurring_expenses': recurring_expenses,
        'non_recurring_expenses': non_recurring_expenses,

        'monthly_totals': monthly_totals,

        'mom_change': mom_change,
        'mom_change_label': mom_change_label,

        'highest_spending_month': highest_spending_month,
        'lowest_spending_month': lowest_spending_month,

        'selected_month': selected_month,
        'selected_budget': selected_budget,
        'selected_actual': selected_actual,
        'selected_remaining': selected_remaining,
        'selected_status': selected_status,
        'selected_status_class': selected_status_class,
        'selected_utilization': selected_utilization,

        'available_months': available_months,
        'selected_month_label': selected_month_label,
    }

    return render(
        request,
        'analytics.html',
        context
    )