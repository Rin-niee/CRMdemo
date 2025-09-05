from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('register-client/', views.ClientRegister, name='register-client'),
    path('register-manager/', views.ManagerRegister, name='register-manager'),
    path('login/', views.user_login, name='api_login'),
    path('logout/', views.user_logout, name='api_logout'),

    path('bid/all/', views.all_bid, name="all_bid"),
    path('bid/', views.create_bid, name="create_bid"),
    path('bid/<int:pk>/', views.bid_one, name="bid"),

    path('order/', views.create_order, name="create_order"),
    path('order/all/', views.all_orders, name="all_orders"),
    path('order/<int:pk>/', views.order, name="order"),
    path('order/<int:pk>/status/', views.status_order, name="status"),
    path('order/<int:pk>/upload_doc/', views.upload_doc,name="doc"),

    path('company/', views.create_company, name="create_company"),
    path('company/all/', views.all_company, name="all_company"),
    path('company/<int:pk>/', views.company, name="company"),
    path('company/add/', views.company_add, name="company_add"),
    path('company/<int:company_id>/employee/<int:user_id>/remove/',  views.remove_employee, name="remove_employee")
]
