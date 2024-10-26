# products/admin.py

from django.contrib import admin
from .models import Product, Review

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at', 'is_active')
    list_filter = ('is_active', 'rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'comment')
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_active=True)
    approve_reviews.short_description = 'Одобрить выбранные отзывы'

    def reject_reviews(self, request, queryset):
        queryset.update(is_active=False)
    reject_reviews.short_description = 'Отклонить выбранные отзывы'

admin.site.register(Product)
admin.site.register(Review, ReviewAdmin)
