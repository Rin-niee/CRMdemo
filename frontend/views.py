from django.shortcuts import render, get_object_or_404

<<<<<<< Updated upstream
<<<<<<< Updated upstream
# Create your views here.
def create_orders(request):
    return render(request, "frontend/create_orders.html")
=======
=======
>>>>>>> Stashed changes
#создание заказа
def create_orders(request):
    return render(request, "frontend/create_orders.html")
#список всех заказов
def all_orders(request):
    return render(request, "frontend/all_orders.html")
#заказ
def order(request, pk):
    return render(request, "frontend/order.html")
#статусы к заказу
def statuses(request, pk):
    return render(request, "frontend/status.html")
# документы к заказу
def upload_doc_status(request, pk):
    return render(request, "frontend/upload.html")
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

def all_orders(request):
    return render(request, "frontend/all_orders.html")

def order(request, pk):
    return render(request, "frontend/order.html")

def statuses(request, pk):
    return render(request, "frontend/status.html")

<<<<<<< Updated upstream
def upload_doc_status(request, pk):
    return render(request, "frontend/upload.html")
=======

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

# страница уведомлений
@login_required(login_url='/login/')
def notifications(request):
    return render(request, "frontend/notifications.html")

# страница чатов
@login_required(login_url='/login/')
def chats(request):
<<<<<<< Updated upstream
    return render(request, "frontend/chats.html")
>>>>>>> Stashed changes
=======
    return render(request, "frontend/chats.html")
>>>>>>> Stashed changes
