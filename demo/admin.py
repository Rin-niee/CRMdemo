from django.contrib import admin
from .models import Client, Status_orders, Order, TGUsers

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'comment_preview', 'orders_count')
    list_filter = ('name',)
    search_fields = ('name', 'phone', 'comment')
    readonly_fields = ('orders_count',)
    
    def comment_preview(self, obj):
        if obj.comment:
            return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment
        return 'Нет комментария'
    comment_preview.short_description = 'Комментарий'
    
    def orders_count(self, obj):
        return obj.order_set.count()
    orders_count.short_description = 'Количество заказов'

@admin.register(Status_orders)
class StatusOrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'current_status', 'payment_doc', 'parking_doc', 'preparation_doc', 
                   'bill_of_lading_doc', 'port_transport_doc', 'port_arrival_doc', 'order_received_doc')
    list_filter = ('current_status',)
    readonly_fields = ('id',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'current_status')
        }),
        ('Документы', {
            'fields': ('payment_doc', 'parking_doc', 'preparation_doc', 'bill_of_lading_doc', 
                      'port_transport_doc', 'port_arrival_doc', 'order_received_doc'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_name', 'VIN', 'number_order', 'number_note', 'date', 'current_status')
    list_filter = ('date', 'status__current_status', 'client__name')
    search_fields = ('VIN', 'number_order', 'number_note', 'client__name', 'client__phone')
    readonly_fields = ('id', 'date')
    date_hierarchy = 'date'
    
    def client_name(self, obj):
        return obj.client.name if obj.client else 'Нет клиента'
    client_name.short_description = 'Клиент'
    
    def current_status(self, obj):
        return obj.status.current_status if obj.status else 'Нет статуса'
    current_status.short_description = 'Статус'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'client', 'VIN', 'number_order', 'number_note', 'date')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('client', 'status')

@admin.register(TGUsers)
class TGUsersAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_id')
    search_fields = ('chat_id',)
    readonly_fields = ('id',)
    ordering = ('id',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'chat_id')
        }),
    )

# Настройка админки
admin.site.site_header = "CRM Demo - Администрирование"
admin.site.site_title = "CRM Demo Admin"
admin.site.index_title = "Добро пожаловать в CRM Demo"
