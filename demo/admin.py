from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.utils import timezone


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
    list_display = ('is_admin', 'id')
    search_fields = ('is_admin',)
    ordering = ('is_admin',)
    list_per_page = 20

@admin.register(Companies)
class CompaniesAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_approved')
    actions = ['approve_company', 'reject_company']

    def approve_company(self, request, queryset):
        queryset.update(is_approved=True)

    approve_company.short_description = "Одобрить компанию"

    def reject_company(self, request, queryset):
        for company in queryset:
            company.is_approved = False
            company.save()
            company.delete()  # удаляем сразу
    reject_company.short_description = "Отклонить компанию"


@admin.register(Dealers)
class DealersAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'company_name', 'phone', 'address', 'photo_preview')
    search_fields = ('name', 'company_name', 'phone', 'address')
    ordering = ('name','company_name',)

    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="80"/>', obj.photo.url)
        return "-"
    photo_preview.short_description = 'Фото'

@admin.register(CarsPhoto)
class CarsPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'photo_preview')
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100"/>', obj.photo.url)
        return "-"
    photo_preview.short_description = 'Фото'

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone', "name")
    search_fields = ('username', 'email', 'phone', "name")
    ordering = ( "name",)

@admin.register(bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'brand', 'model', 'year', 'status', 'dealer')
    search_fields = ('brand', 'model', 'user__username', 'company__name', 'dealer__name')
    list_filter = ('status', 'company', 'dealer')
    ordering = ('-id',)
    filter_horizontal = ('photo',)
    exclude = ('user', 'manager', 'opened_at', 'arrived_time', 'checklist_point1', 'checklist_point2', 'deadline')
    readonly_fields = ('company',)

    def save_model(self, request, obj, form, change):
        # Если статус стал "open" и opened_at еще не задан
        if obj.status == "open" and not obj.opened_at:
            obj.opened_at = timezone.now()
        super().save_model(request, obj, form, change)
        


@admin.register(user_company)
class user_companyAdmin(admin.ModelAdmin):
    pass

admin.site.site_header = "CRM Demo - Администрирование"
admin.site.site_title = "CRM Demo"
admin.site.index_title = "Панель управления"
