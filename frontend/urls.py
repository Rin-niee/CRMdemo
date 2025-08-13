from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('order/', views.create_orders, name="create_order"),
    path('', views.all_orders, name="all_orders"),
    path('order/<int:pk>/', views.order, name="order"),
    path('order/<int:pk>/status/', views.statuses, name="status"),
    path('order/<int:pk>/upload_doc/', views.upload_doc_status, name="doc"),
]

