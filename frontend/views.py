from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

# #создание заказа
# def create_orders(request):
#     return render(request, "frontend/create_orders.html")
# #список всех заказов
# def all_orders(request):
#     return render(request, "frontend/all_orders.html")
# #заказ
# def order(request, pk):
#     return render(request, "frontend/order.html")
# #статусы к заказу
# def statuses(request, pk):
#     return render(request, "frontend/status.html")
# # документы к заказу
# def upload_doc_status(request, pk):
#     return render(request, "frontend/upload.html")

# регистрация клиента
def ClientRegister(request):
    return render(request, "frontend/registration.html")
# вход в клиента
def login(request):
    return render(request, "frontend/login.html")

#все заявки
@login_required(login_url='/login/')
def bids(request):
    return render(request, "frontend/all_bids.html")
#заявка конкретная
@login_required(login_url='/login/')
def bid(request, pk):
    return render(request, "frontend/bid.html")
# создание заявки
@login_required(login_url='/login/')
def create_bid(request):
    return render(request, "frontend/create_bid.html")



#все компании
@login_required(login_url='/login/')
def create_company(request):
    return render(request, "frontend/create_company.html")
#компания конкретная
@login_required(login_url='/login/')
def all_company(request):
    return render(request, "frontend/all_company.html")
# создание компании
@login_required(login_url='/login/')
def company(request, pk):
    return render(request, "frontend/company.html")

# создание компании
@login_required(login_url='/login/')
def company_add(request):
    return render(request, "frontend/company_add.html")