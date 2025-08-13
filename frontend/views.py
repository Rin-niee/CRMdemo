from django.shortcuts import render, get_object_or_404
from demo.models import Order, Client, Status_orders

# Create your views here.
def create_orders(request):
    return render(request, "frontend/create_orders.html")

def all_orders(request):
    return render(request, "frontend/all_orders.html")

def order(request, pk):
    return render(request, "frontend/order.html")

def statuses(request, pk):
    return render(request, "frontend/status.html")

def upload_doc_status(request, pk):
    return render(request, "frontend/upload.html")