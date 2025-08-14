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
    files = request.FILES.getlist('file')

    allowed_fields = [
        'payment', 'parking', 'preparation', 'bill_of_lading',
        'port_transport', 'port_arrival', 'order_received'
    ]

    if not doc_type or not files:
        return Response({"error": "doc_type and files are required"}, status=400)

    if doc_type not in allowed_fields:
        return Response({"error": "Invalid doc_type"}, status=400)
    idx = allowed_fields.index(doc_type)
    for prev_field in allowed_fields[:idx]:
        if not status_obj.files.filter(doc_type=prev_field).exists():
            return Response(
                {"error": f"Нельзя загружать {doc_type}, пока не загружены файлы для {prev_field}"},
                status=400
            )
    uploaded_files = []
    for f in files:
        file_obj = StatusFile.objects.create(file=f, doc_type=doc_type)
        status_obj.files.add(file_obj)
        uploaded_files.append(file_obj)

    update_status_by_workflow(status_obj)

    status_labels = {
        "payment": "Оплата",
        "parking": "Прибытие авто на парковку",
        "preparation": "Подготовка к экспорту",
        "bill_of_lading": "Имя для коносамента",
        "port_transport": "Транспортировка в порт",
        "port_arrival": "Прибытие в порт",
        "order_received": "Заказ получен"
    }

    label = status_labels.get(doc_type, "Неизвестный статус")
    next_label = "финальный статус"
    if idx + 1 < len(allowed_fields):
        next_label = status_labels.get(allowed_fields[idx + 1], "следующий статус")

    send_telegram_message(f"🚗 Заказ #{pk} перешел из статуса <b>{label}</b> в статус <b>{next_label}</b>")
    send_telegram_documents_group(uploaded_files, caption=f"Файлы по статусу: {label}")

    serializer = Status_ordersSerializer(status_obj)
    return Response(serializer.data, status=200)


def update_status_by_workflow(status_obj):
    allowed_fields = [
        'payment', 'parking', 'preparation', 
        'bill_of_lading', 'port_transport', 
        'port_arrival', 'order_received'
    ]

    for field in allowed_fields:
        if not status_obj.files.filter(doc_type=field).exists():
            status_obj.current_status = field
            status_obj.save()
            return
    status_obj.current_status = 'order_received'
    status_obj.save()


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


def send_telegram_documents_group(file_objs, caption=None):
    """
    file_objs — список объектов StatusFile, уже сохранённых
    caption — подпись для первого файла
    """
    for user in TGUsers.objects.all():
        media = []
        files_payload = {}

        for i, sf in enumerate(file_objs):
            path = sf.file.path
            media.append({
                "type": "document",
                "media": f"attach://file{i}",
                "caption": caption if i == 0 else ""
            })
            files_payload[f"file{i}"] = (sf.file.name, open(path, "rb"), "application/octet-stream")

        data = {
            "chat_id": user.chat_id,
            "media": str(media).replace("'", '"')
        }

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMediaGroup",
            data=data,
            files=files_payload
        )