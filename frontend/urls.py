from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('registration/', views.ClientRegister, name="registration"),
    path('login/', views.login, name="login"),
    
    path('bid/all/', views.bids, name="bids"),
    path('bid/<int:pk>/', views.bid, name="bid"),
    path('bid/', views.create_bid, name="create_bid"),
    
    path('', views.all_orders, name="all_orders"),
    path('order/', views.create_orders, name="create_orders"),
    path('order/<int:pk>/', views.order, name="order"),
    
    path('order/<int:pk>/status/', views.statuses, name="status"),
    path('order/<int:pk>/upload_doc/', views.upload_doc_status, name="doc"),
    
    path('company/', views.create_company, name="create_company"),
    path('company/all/', views.all_company, name="all_company"),
    path('company/<int:pk>/', views.company, name="company"),
    path('company/add', views.company_add, name="company_add"),
    
    path('notifications/', views.notifications, name="notifications"),
    path('chats/', views.chats, name="chats"),
]

