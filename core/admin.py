from django.contrib import admin

from .models import Pincode, ToolRun, ToolRunFile, CofWorkbook


@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ('pin', 'city', 'state', 'location_type')
    list_filter = ('location_type', 'state')
    search_fields = ('pin', 'city', 'state')


class ToolRunFileInline(admin.TabularInline):
    model = ToolRunFile
    extra = 0


@admin.register(ToolRun)
class ToolRunAdmin(admin.ModelAdmin):
    list_display = ('tool', 'reference', 'user', 'status', 'created_at')
    list_filter = ('tool', 'status', 'created_at')
    search_fields = ('reference', 'detail')
    readonly_fields = ('created_at',)
    inlines = [ToolRunFileInline]


@admin.register(CofWorkbook)
class CofWorkbookAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'uploaded_by', 'is_active', 'uploaded_at')
    list_filter = ('is_active', 'uploaded_at')
    search_fields = ('original_name',)
    readonly_fields = ('uploaded_at',)
