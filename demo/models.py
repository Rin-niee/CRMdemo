from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    comment = models.TextField(blank=True)

class StatusFile(models.Model):
    DOC_TYPE_CHOICES = [
        ("payment", "Оплата"),
        ("parking", "Прибытие на парковку"),
        ("preparation", "Подготовка к экспорту"),
        ("bill_of_lading", "Коносамент"),
        ("port_transport", "Транспортировка в порт"),
        ("port_arrival", "Прибытие в порт"),
        ("order_received", "Заказ получен"),
    ]

    file = models.FileField(upload_to='docs/%Y/%m/%d/')
    doc_type = models.CharField(max_length=50, choices=DOC_TYPE_CHOICES)
    uploaded_at = models.DateTimeField(auto_now_add=True)


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
    files = models.ManyToManyField(StatusFile, blank=True, related_name='orders')

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