# reports/admin.py
from django.contrib import admin
from django.utils import timezone
from .models import FarmerReport, CustomerReport

@admin.register(FarmerReport)
class FarmerReportAdmin(admin.ModelAdmin):
    list_display = ['subject', 'farmer', 'category', 'is_solved', 'created_at']
    list_filter = ['is_solved', 'category', 'created_at']
    search_fields = ['subject', 'farmer__user__username', 'farmer__user__email']
    readonly_fields = ['created_at']
    actions = ['mark_as_solved', 'mark_as_unsolved']

    def mark_as_solved(self, request, queryset):
        queryset.update(is_solved=True, solved_at=timezone.now())
    mark_as_solved.short_description = "Mark selected reports as Solved"

    def mark_as_unsolved(self, request, queryset):
        queryset.update(is_solved=False, solved_at=None)
    mark_as_unsolved.short_description = "Mark selected reports as Unsolved"

@admin.register(CustomerReport)
class CustomerReportAdmin(admin.ModelAdmin):
    list_display = ['subject', 'customer', 'category', 'is_solved', 'created_at']
    list_filter = ['is_solved', 'category', 'created_at']
    search_fields = ['subject', 'customer__user__username', 'customer__user__email']
    readonly_fields = ['created_at']
    actions = ['mark_as_solved', 'mark_as_unsolved']

    def mark_as_solved(self, request, queryset):
        queryset.update(is_solved=True, solved_at=timezone.now())
    mark_as_solved.short_description = "Mark selected reports as Solved"

    def mark_as_unsolved(self, request, queryset):
        queryset.update(is_solved=False, solved_at=None)
    mark_as_unsolved.short_description = "Mark selected reports as Unsolved"