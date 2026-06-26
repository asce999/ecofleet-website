from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db import connection
from django.conf import settings
import os

from .models import Pincode, ToolRun, ToolRunFile, CofWorkbook, AttendanceWorkbook, BtplWorkbook, FtlWorkbook

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

def diagnostics_view(request):
    context = dict(
        admin.site.each_context(request),
        title="System Diagnostics"
    )
    
    # DB Status
    try:
        connection.ensure_connection()
        context['db_status'] = 'ok'
    except Exception:
        context['db_status'] = 'error'

    context['version'] = '1.0.0'
    
    # Last operations
    context['last_attendance'] = AttendanceWorkbook.objects.order_by('-uploaded_at').first()
    context['last_btpl'] = BtplWorkbook.objects.order_by('-created_at').first()
    context['last_ftl'] = FtlWorkbook.objects.order_by('-uploaded_at').first()
    context['last_cof'] = CofWorkbook.objects.order_by('-uploaded_at').first()
    
    # Recent errors from log file
    error_log_path = os.path.join(settings.BASE_DIR, 'logs', 'errors.log')
    if os.path.exists(error_log_path):
        with open(error_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            context['recent_errors'] = "".join(lines[-50:])
    else:
        context['recent_errors'] = ""

    return TemplateResponse(request, "admin/diagnostics.html", context)

# Monkey-patch admin get_urls
_orig_get_urls = admin.site.get_urls

def get_admin_urls():
    urls = _orig_get_urls()
    custom_urls = [
        path('diagnostics/', admin.site.admin_view(diagnostics_view), name='diagnostics'),
    ]
    return custom_urls + urls

admin.site.get_urls = get_admin_urls

