from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_expense, name='add_expense'),
    path('budget/', views.set_budget, name='set_budget'),
    path('monthly-budget/', views.monthly_budget, name='monthly_budget'),
    path(
    'optimize/',views.optimize_spending,name='optimize_spending'),
    path('analytics/', views.spending_analytics, name='spending_analytics'),
]