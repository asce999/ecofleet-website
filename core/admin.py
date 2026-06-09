from django.contrib import admin
from .models import Pincode, ToolRun


@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ('pin', 'city', 'state', 'location_type')
    list_filter = ('location_type', 'state')
    search_fields = ('pin', 'city', 'state')


@admin.register(ToolRun)
class ToolRunAdmin(admin.ModelAdmin):
    list_display = ('tool', 'reference', 'user', 'status', 'created_at')
    list_filter = ('tool', 'status', 'created_at')
    search_fields = ('reference', 'detail')
    readonly_fields = ('created_at',)