from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
<<<<<<< Updated upstream
=======
    path('register-client/', views.ClientRegister, name='register-client'),
    path('register-manager/', views.ManagerRegister, name='register-manager'),
    path('login/', views.user_login, name='api_login'),
    path('logout/', views.user_logout, name='api_logout'),

    path('bid/all/', views.all_bid, name="all_bid"),
    path('bid/', views.create_bid, name="create_bid"),
    path('bid/<int:pk>/', views.bid_one, name="bid"),
    path('bid/<int:pk>/update/', views.update_bid_topics, name="update_bid_topics"),
    

>>>>>>> Stashed changes
    path('order/', views.create_order, name="create_order"),
    path('order/all/', views.all_orders, name="all_orders"),
    path('order/<int:pk>/', views.order, name="order"),
    path('order/<int:pk>/status/', views.status_order, name="status"),
    path('order/<int:pk>/upload_doc/', views.upload_doc,name="doc"),
<<<<<<< Updated upstream
=======

    path('company/', views.create_company, name="create_company"),
    path('company/all/', views.all_company, name="all_company"),
    path('company/<int:pk>/', views.company, name="company"),
    path('company/add/', views.company_add, name="company_add"),
    path('company/<int:company_id>/employee/<int:user_id>/remove/',  views.remove_employee, name="remove_employee"),
    path('notifications/', views.notifications_api, name="company_add"),
    path("notifications/<str:pk>/toggle_read/", views.toggle_read_api, name="toggle_read_api"),

    path('message/', views.get_all_message, name="get_all_message"),
    path('message/<int:pk>', views.get_message, name="get_message"),
    path("message/create/", views.create_message, name="create_message")
>>>>>>> Stashed changes
]

