from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    comment = models.TextField(blank=True)

class Status_orders(models.Model):
    STATUS_CHOICES = [
        ("payment", "Оплата"),
        ("parking", "Прибытие на парковку"),
        ("preparation", "Подготовка к экспорту"),
        ("bill_of_lading", "Коносамент"),
        ("port_transport", "Транспортировка в порт"),
        ("port_arrival", "Прибытие в порт"),
        ("order_received", "Заказ получен"),
    ]

    current_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="payment")

    payment_doc = models.FileField(upload_to="docs/payment/", blank=True, null=True)
    parking_doc = models.FileField(upload_to="docs/parking/", blank=True, null=True)
    preparation_doc = models.FileField(upload_to="docs/preparation/", blank=True, null=True)
    bill_of_lading_doc = models.FileField(upload_to="docs/bill_of_lading/", blank=True, null=True)
    port_transport_doc = models.FileField(upload_to="docs/port_transport/", blank=True, null=True)
    port_arrival_doc = models.FileField(upload_to="docs/port_arrival/", blank=True, null=True)
    order_received_doc = models.FileField(upload_to="docs/order_received/", blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.current_status}"

class Order(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    VIN =  models.CharField(max_length=100)
    number_order = models.CharField(max_length=100)
    number_note = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    status = models.ForeignKey(Status_orders, on_delete=models.CASCADE)


class TGUsers(models.Model):
    chat_id = models.IntegerField()