from rest_framework import serializers
from .models import *

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



