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

<<<<<<< Updated upstream

class TGUsers(models.Model):
    chat_id = models.IntegerField()
=======
class Groups(models.Model):
    tg_id=models.BigIntegerField()
    inspection_id = models.IntegerField()
    clients_id = models.IntegerField()
    calls_id = models.IntegerField()
    class Meta:
        db_table = "groups"
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

class TGUsers(models.Model):
    id = models.BigIntegerField(primary_key=True,verbose_name="ID пользователя в телеграм")
    is_admin = models.BooleanField(default=0)
    is_caller = models.BooleanField(default=0)
    group = models.ForeignKey(Groups, on_delete=models.CASCADE, null=True, blank = True)
    class Meta:
        db_table = "users"
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"
    def __str__(self):
        return str(self.id)

class Dealers(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True,verbose_name="Контактное лицо")
    company_name = models.CharField(max_length=100,  verbose_name="Наименование компании(обязательно)")
    phone = models.CharField(max_length=100, blank=True, null=True, verbose_name="Телефон компании")
    address = models.CharField(max_length=100, blank=True, null=True, verbose_name="Адрес компании")
    photo = models.FileField(upload_to='dealers/%Y/%m/%d/', blank=True)
    class Meta:
        db_table = "dealers"
        verbose_name = "Дилер"
        verbose_name_plural = "Дилеры"
    def __str__(self):
        return self.company_name or "Без названия"

#заявка и прочее
class bid(models.Model):
    STATUS_CHOICES = [
        ('disable', 'Disable'),
        ('open', 'Open'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Пользователь")
    company = models.ForeignKey(Companies, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Компания")

    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Бренд")
    model = models.CharField(max_length=100, blank=True, null=True, verbose_name="Модель")

    year= models.IntegerField(blank=True, null=True, verbose_name="Год")

    mileage = models.IntegerField(blank=True, null=True, verbose_name="Пробег")
    fuel_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Тип топлива")
    drive_type = models.CharField(max_length=100, blank=True, null=True, verbose_name="Тип привода")

    engine = models.CharField(max_length=100, blank=True, null=True, verbose_name="Двигатель")
    power = models.CharField(max_length=100, blank=True, null=True, verbose_name="Мощность двигателя")
    transmission = models.CharField(max_length=100, blank=True, null=True, verbose_name="Коробка передач")
    
    create_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='disable', verbose_name="Статус заявки")
    manager = models.ForeignKey(TGUsers, on_delete=models.CASCADE, blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True, verbose_name="Исполняющий менеджер")
    url_users =  models.CharField(max_length=500, blank=True, null=True, verbose_name="Исходная ссылка на авто")
    url =  models.CharField(max_length=500, blank=True, null=True, verbose_name="Конечная ссылка на авто")
    dealer = models.ForeignKey(Dealers, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Дилер")
    opened_at = models.DateTimeField(blank=True, null=True)
    arrived_time = models.DateTimeField(blank=True, null=True)
    thread_id = models.BigIntegerField(blank=True, null=True)
    checklist_point1 = models.CharField(max_length=100, null=True, blank=True, verbose_name="Состояние бампера")
    checklist_point2 = models.CharField(max_length=100, null=True, blank=True, verbose_name="Уровень топлива в баке")
    shown_to_bot = models.BooleanField(default=False, verbose_name="Уведомление боту показано")
    in_stock = models.BooleanField(default=False, verbose_name="Авто в наличии")
    caller_saw = models.BooleanField(default=False, verbose_name="Отправлено в чат просмотрщиков")
    class Meta:
        db_table = "bid"
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
    def __str__(self):
        return f"Заявка #{self.id} — {self.brand} {self.model} ({self.year})"
    
class CarsPhoto(models.Model):
    bid = models.ForeignKey(bid, on_delete=models.CASCADE, blank=True, null=True, related_name="photos")
    file_url = models.FileField() 
    def __str__(self):
        return f"Photo for Order #{self.bid.id}" 
    class Meta:
        db_table = "photo"
        verbose_name = "Фото"
        verbose_name_plural = "Фото"

class ChatMessage(models.Model):
    bid = models.ForeignKey(bid, on_delete=models.CASCADE)
    chat_id = models.BigIntegerField()
    message_thread_id = models.BigIntegerField()
    message_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    username = models.CharField(max_length=255, blank=True)
    topic_name = models.CharField(max_length=255, blank=True)
    text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    to_bot = models.BooleanField(default=False)

#хранение файлов из сообщений
class ChatMedia(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='media')
    file_type = models.CharField(max_length=20)
    file_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# модель для сохранения смс.
class ChatMessage(models.Model):
    bid = models.ForeignKey(bid, on_delete=models.CASCADE)  # какая заявка
    chat_id = models.BigIntegerField()                     # Telegram группа
    message_thread_id = models.BigIntegerField()           # тема в форуме
    message_id = models.BigIntegerField()                 # id сообщения Telegram
    user_id = models.BigIntegerField()                     # кто написал
    username = models.CharField(max_length=255, blank=True) # ник
    topic_name = models.CharField(max_length=255, blank=True) # ник
    text = models.TextField(null=True, blank=True)                              # само сообщение
    created_at = models.DateTimeField(auto_now_add=True)   # время
    to_bot = models.BooleanField(default=False)   # время

#хранение файлов из сообщений
class ChatMedia(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='media')
    file_type = models.CharField(max_length=20)
    file_url = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

>>>>>>> Stashed changes
