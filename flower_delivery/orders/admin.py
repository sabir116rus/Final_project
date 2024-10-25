# orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem
from django.utils.html import format_html

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 1

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'delivery_date', 'delivery_time', 'delivery_place', 'colored_status', 'total_price']
    list_filter = ['status', 'created_at', 'user']
    search_fields = ['id', 'user__username', 'user__email']
    inlines = [OrderItemInline]
    ordering = ['-created_at']
    actions = ['mark_as_accepted', 'mark_as_in_progress', 'mark_as_in_delivery', 'mark_as_completed', 'mark_as_canceled']
    readonly_fields = ['user', 'created_at', 'total_price', 'delivery_date', 'delivery_time', 'delivery_place']

    # Остальной код остается без изменений


    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status == 'canceled':
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields

    def colored_status(self, obj):
        color = obj.status_color()
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())

    colored_status.short_description = 'Статус'

    def mark_as_accepted(self, request, queryset):
        queryset.update(status='accepted')
    mark_as_accepted.short_description = 'Отметить выбранные заказы как "Принят к работе"'

    def mark_as_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
    mark_as_in_progress.short_description = 'Отметить выбранные заказы как "Находится в работе"'

    def mark_as_in_delivery(self, request, queryset):
        queryset.update(status='in_delivery')
    mark_as_in_delivery.short_description = 'Отметить выбранные заказы как "В доставке"'

    def mark_as_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_as_completed.short_description = 'Отметить выбранные заказы как "Выполнен"'

    def mark_as_canceled(self, request, queryset):
        queryset.update(status='canceled')
    mark_as_canceled.short_description = 'Отметить выбранные заказы как "Отменен"'
