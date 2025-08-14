from django.contrib import admin
from .models import Client, StatusFile, Status_orders, Order, TGUsers


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'comment', 'id')
    list_filter = ('name',)
    search_fields = ('name', 'phone', 'comment')
    ordering = ('name',)
    list_per_page = 20


@admin.register(StatusFile)
class StatusFileAdmin(admin.ModelAdmin):
    list_display = ('doc_type', 'file', 'uploaded_at', 'id')
    list_filter = ('doc_type', 'uploaded_at')
    search_fields = ('doc_type',)
    ordering = ('-uploaded_at',)
    list_per_page = 20
    readonly_fields = ('uploaded_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('doc_type', 'file')
        }),
        ('Метаданные', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Status_orders)
class StatusOrdersAdmin(admin.ModelAdmin):
    list_display = ('id', 'current_status', 'get_files_count')
    list_filter = ('current_status',)
    search_fields = ('current_status',)
    ordering = ('id',)
    list_per_page = 20
    filter_horizontal = ('files',)
    
    def get_files_count(self, obj):
        return obj.files.count()
    get_files_count.short_description = 'Количество файлов'
    
    fieldsets = (
        ('Статус заказа', {
            'fields': ('current_status',)
        }),
        ('Файлы', {
            'fields': ('files',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'VIN', 'number_order', 'number_note', 'date', 'status')
    list_filter = ('date', 'status__current_status', 'client')
    search_fields = ('VIN', 'number_order', 'number_note', 'client__name')
    ordering = ('-date',)
    list_per_page = 20
    readonly_fields = ('date',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('client', 'VIN', 'number_order', 'number_note')
        }),
        ('Статус и дата', {
            'fields': ('status', 'date'),
            'classes': ('collapse',)
        }),
    )
    
    autocomplete_fields = ['client', 'status']


@admin.register(TGUsers)
class TGUsersAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'id')
    search_fields = ('chat_id',)
    ordering = ('chat_id',)
    list_per_page = 20


# Настройка заголовка админки
admin.site.site_header = "CRM Demo - Администрирование"
admin.site.site_title = "CRM Demo"
admin.site.index_title = "Панель управления"
