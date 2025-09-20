from django.utils import timezone
from rest_framework import serializers
from .models import *
from collections import defaultdict

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = "__all__"

class StatusFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusFile
        fields = ['id', 'file', 'doc_type', 'uploaded_at']

class Status_ordersSerializer(serializers.ModelSerializer):
    files = StatusFileSerializer(many=True)

    class Meta:
        model = Status_orders
        fields = ['id', 'current_status', 'files']
        
class OrdersSerializer(serializers.ModelSerializer):
    client = ClientSerializer()
    status = Status_ordersSerializer(read_only=True)
    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = ['status']

    def create(self, validated_data):
        client_data = validated_data.pop('client')
        client = Client.objects.create(**client_data)
        status_obj = Status_orders.objects.create(current_status='payment')
        order = Order.objects.create(client=client, status=status_obj, **validated_data)
        return order


class BidsSerializer(serializers.ModelSerializer):
    # user = serializers.PrimaryKeyRelatedField(
    #     queryset=User.objects.all(), required=False
    # )
    # user_username = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()

    class Meta:
        model = bid
        fields = "__all__"
        read_only_fields = ['status']

    def get_user_username(self, obj):
        return obj.user.username if obj.user else None

    def get_company_name(self, obj):
        return obj.company.name if obj.company else None
    def create(self, validated_data):
        # user = validated_data.get('user') or self.context['request'].user
        # validated_data['user'] = user
        validated_data['status'] = 'ring'
        # user_comp = user_company.objects.filter(user_id=user).first()
        # if not user_comp or not user_comp.company_id:
        #     raise serializers.ValidationError("Вы не состоите ни в одной компании, заявка не может быть создана.")
        # user_comp = user_company.objects.filter(user_id=user).first()
        # if user_comp and user_comp.company_id:
        #     validated_data['company'] = user_comp.company_id
        # else:
        #     validated_data['company'] = None
        bid_obj = bid.objects.create(**validated_data)
        return bid_obj

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "role", "name"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
    

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class UserCompanySerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='user_id.name')
    id = serializers.IntegerField(source='user_id.id')
    print(name)
    class Meta:
        model = user_company
        fields = ['id', 'name', 'role']

class CompanySerializer(serializers.ModelSerializer):
    employees = serializers.SerializerMethodField()
    current_user_id = serializers.SerializerMethodField()
    current_user_role = serializers.SerializerMethodField()

    class Meta:
        model = Companies
        fields = ["id","name","INN","adress","website","employees","current_user_id","current_user_role", "is_approved"]

    def get_employees(self, obj):
        qs = user_company.objects.filter(company_id=obj)
        return UserCompanySerializer(qs, many=True).data

    def get_current_user_id(self, obj):
        return self.context['request'].user.id

    def get_current_user_role(self, obj):
        uc = user_company.objects.filter(company_id=obj, user_id=self.context['request'].user).first()
        return uc.role if uc else None

    def create(self, validated_data):
        company = Companies.objects.create(**validated_data, is_approved=False)
        user = self.context['request'].user
        user_company.objects.create(user_id=user, company_id=company, role='owner')
        return company
    

class ChatMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMedia
        fields = ['file_url', 'file_type']   
    
class ChatMessageSerializer(serializers.ModelSerializer):
    media = ChatMediaSerializer(many=True, read_only=True)
    class Meta:
        model = ChatMessage
        fields = ['bid', 'chat_id', 'message_thread_id', 'message_id', 'user_id', 
                  'username', 'topic_name', 'text', 'created_at', 'to_bot', 'media']
        
class GroupedChatMessageSerializer(serializers.Serializer):
    grouped = serializers.SerializerMethodField()

    def get_grouped(self, obj):
        grouped = defaultdict(list)
        for m in obj:
            media_serialized = ChatMediaSerializer(m.media.all(), many=True).data
            grouped[m.message_thread_id].append({
                "bid_id": m.bid_id,
                "chat_id": m.chat_id,
                "message_thread_id": m.message_thread_id,
                "message_id": m.message_id,
                "user_id": m.user_id,
                "username": m.username,
                "text": m.text,
                "topic_name": m.topic_name,
                "created_at": m.created_at.isoformat(),
                "media": media_serialized
            })
        return grouped