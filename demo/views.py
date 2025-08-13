from django.shortcuts import get_object_or_404, render
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from telegram import InputMediaDocument
from demo.serializers import *
from rest_framework import status
from .workflow import WORKFLOW_STEPS
import requests
from demo.models import TGUsers
from io import BytesIO

BOT_TOKEN = "7519143065:AAGYsojc-fz9dxY4S1VFQE3UvOxICoNK7ns"

def send_telegram_message(text):
    for user in TGUsers.objects.all():
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={
                "chat_id": user.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
        )


import requests
from io import BytesIO

def send_telegram_documents_group(files_list, caption=None):
    """
    files_list — список объектов InMemoryUploadedFile или TemporaryUploadedFile
    caption — текст для первого файла
    """
    for user in TGUsers.objects.all():
        media = []
        for i, f in enumerate(files_list):
            f.seek(0)
            # Чтобы Telegram понял файл, нужно передать как multipart/form-data
            media.append({
                "type": "document",
                "media": f"attach://file{i}",  # привязка к multipart
                "caption": caption if i == 0 else ""  # подпись только для первого
            })

        # Собираем files для multipart
        files_payload = {f"file{i}": (f.name, f, "application/octet-stream") for i, f in enumerate(files_list)}

        data = {
            "chat_id": user.chat_id,
            "media": str(media).replace("'", '"')  # Telegram API требует JSON
        }

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup",
            data=data,
            files=files_payload
        )



@api_view(['POST'])
def create_order(request):
    serializer = OrdersSerializer(data = request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status =status.HTTP_201_CREATED)
    else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def all_orders(request):
    orders = Order.objects.all()
    serializer = OrdersSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    serializer = OrdersSerializer(order)
    return Response(serializer.data)

@api_view(['GET'])
def status_order(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status = order.status
    serializer = Status_ordersSerializer(status)
    return Response(serializer.data)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_doc(request, pk):
    status_obj = get_object_or_404(Status_orders, pk=pk)
    doc_type = request.query_params.get('doc_type')
    file = request.FILES.get('file')

    allowed_fields = [
        'payment_doc', 'parking_doc', 'preparation_doc', 'bill_of_lading_doc',
        'port_transport_doc', 'port_arrival_doc', 'order_received_doc'
    ]

    if not doc_type or not file:
        return Response({"error": "doc_type and file are required"}, status=400)

    if doc_type not in allowed_fields:
        return Response({"error": "Invalid doc_type"}, status=400)
    
    idx = allowed_fields.index(doc_type)
    for prev_field in allowed_fields[:idx]:
        if not getattr(status_obj, prev_field):
            return Response(
                {"error": f"Нельзя загружать {doc_type} пока не загружены файлы для {prev_field}"},
                status=400
            )
    setattr(status_obj, doc_type, file)
    update_status_by_workflow(status_obj)
    status_obj.save()

    status_labels = {
        "payment_doc": "Оплата",
        "parking_doc": "Прибытие авто на парковку",
        "preparation_doc": "Подготовка к экспорту",
        "bill_of_lading_doc": "Имя для коносамента",
        "port_transport_doc": "Транспортировка в порт",
        "port_arrival_doc": "Прибытие в порт",
        "order_received_doc": "Заказ получен"
    }
    label = status_labels.get(doc_type, "Неизвестный статус")
    next_label = "финальный статус"
    if idx + 1 < len(allowed_fields):
        next_doc_type = allowed_fields[idx + 1]
        next_label = status_labels.get(next_doc_type, "следующий статус")

    files = request.FILES.getlist('file')
    send_telegram_message(f"🚗 Заказ #{pk} перешел из статуса <b>{label}</b> в статус <b>{next_label}</b>")
    if files:
        send_telegram_documents_group(files, caption=f"Файлы по статусу: {label}")

    serializer = Status_ordersSerializer(status_obj)
    return Response(serializer.data, status=200)


def update_status_by_workflow(status_obj):
    current = status_obj.current_status
    for step in WORKFLOW_STEPS:
        if step["status"] == current:
            required = step["required_files"][0]
            if getattr(status_obj, required):
                if step["next"]:
                    status_obj.current_status = step["next"]
            break