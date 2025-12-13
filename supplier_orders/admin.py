from django.contrib import admin
from .models import Supplier, SupplierOrder, SupplierOrderItem

class SupplierOrderItemInline(admin.TabularInline):
    model = SupplierOrderItem
    extra = 1
    fields = ('sku', 'title', 'quantity', 'price')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'contact_phone', 'created_at')
    search_fields = ('name', 'contact_email')
    list_filter = ('created_at',)

@admin.register(SupplierOrder)
class SupplierOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'date', 'status', 'total')
    list_filter = ('status', 'date', 'supplier')
    search_fields = ('order_number', 'supplier__name', 'tracking_number')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [SupplierOrderItemInline]
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'supplier', 'date', 'status')
        }),
        ('Dates', {
            'fields': ('expected_date', 'received_date')
        }),
        ('Tracking & Notes', {
            'fields': ('tracking_number', 'notes')
        }),
        ('Totals', {
            'fields': ('total',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SupplierOrderItem)
class SupplierOrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'sku', 'title', 'quantity', 'price')
    list_filter = ('order__supplier', 'order__date')
    search_fields = ('sku', 'title', 'order__order_number')
