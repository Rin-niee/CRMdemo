from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from demo.serializers import *
import requests
from demo.models import TGUsers
from django.contrib.auth import authenticate, login, logout
from demo.tasks import *
BOT_TOKEN = "7519143065:AAGYsojc-fz9dxY4S1VFQE3UvOxICoNK7ns"

@api_view(['POST'])
@permission_classes([AllowAny])
def ClientRegister(request):
    data = request.data
    data["role"] = "client"
    serializer = UserRegisterSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Пользователь создан"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def user_login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)
        if user:
            login(request, user) 
            return Response({
                "message": "Успешный вход",
                "user_id": user.id,
                "role": user.role
            }, status=status.HTTP_200_OK)
        return Response({"error": "Неверный логин или пароль"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response({
        "username": request.user.username,
        "id": request.user.id,
        "role": request.user.role
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def user_logout(request):
    logout(request)
    return Response({"message": "Вы вышли из аккаунта"}, status=status.HTTP_200_OK)

@api_view(['POST'])
def ManagerRegister(request):
    if not request.user.is_staff:
        return Response({"error": "Ты не админ"}, status=status.HTTP_403_FORBIDDEN)

    data = request.data
    data["role"] = "manager"
    serializer = UserRegisterSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Менеджер создан"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    orders = order.objects.all()
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
import logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
def create_bid(request):
    serializer = BidsSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        bid_instance = serializer.save()
        url = request.data.get("url_users")
        logger.info(f"ДФДДФФДФД, {bid_instance.id}, {url}")
        if url:
            fetch_car_data_task.delay(bid_instance.id, [url])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_bid(request):
    bids = bid.objects.filter(user=request.user)
    serializer = BidsSerializer(bids, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def bid_one(request, pk):
    bid_one = get_object_or_404(bid, pk=pk)
    serializer = BidsSerializer(bid_one)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_company(request):
    serializer = CompanySerializer(data = request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status =status.HTTP_201_CREATED)
    else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_company(request):
    user_comp = user_company.objects.filter(user_id=request.user).first()
    if user_comp and user_comp.company_id and user_comp.company_id.is_approved:
        serializer = CompanySerializer(user_comp.company_id, context={'request': request})
        return Response([serializer.data])
    else:
        return Response([])


@api_view(['GET'])
def company(request, pk):
    com_one = get_object_or_404(Companies, pk=pk)
    serializer = CompanySerializer(com_one, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_add(request):
    inn = request.data.get("INN")
    password = request.data.get("password")

    try:
        company = Companies.objects.get(INN=inn)
    except Companies.DoesNotExist:
        return Response({"error": "Компания с таким ИНН не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if company.code != password:
        return Response({"error": "Неверный пароль"}, status=status.HTTP_400_BAD_REQUEST)

    user_company.objects.get_or_create(user_id=request.user,company_id=company)

    return Response({"message": f"Вы присоединились к компании {company.name}"})


@api_view(['DELETE'])
def remove_employee(request, company_id, user_id):
    try:
        uc = user_company.objects.get(company_id=company_id, user_id=user_id)
        uc.delete()
        return Response({"detail": "Сотрудник удалён"}, status=status.HTTP_204_NO_CONTENT)
    except user_company.DoesNotExist:
        return Response({"detail": "Сотрудник не найден"}, status=status.HTTP_404_NOT_FOUND)