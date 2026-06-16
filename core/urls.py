from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('services/', views.services, name='services'),
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    re_path(r'^sitemap\.xml/?$', views.sitemap, name='sitemap'),
    path('find-location/', views.find_location, name='find_location'),

    # ── Employee Portal ──
    path('portal/login/', views.portal_login, name='portal_login'),
    path('portal/logout/', views.portal_logout, name='portal_logout'),
    path('portal/', views.dashboard, name='dashboard'),
    path('portal/users/', views.portal_users, name='portal_users'),

    # COF
    path('portal/cof/', views.cof_generator, name='cof_generator'),
    path('portal/cof/workbook/', views.cof_workbook, name='cof_workbook'),
    path('portal/cof/workbook/download/', views.cof_workbook_download, name='cof_workbook_download'),
    path('portal/cof/success/<int:pk>/', views.cof_success, name='cof_success'),
    path('portal/cof/history/', views.cof_history, name='cof_history'),
    path('portal/download/<int:file_id>/', views.download_file, name='download_file'),

    path('portal/morning-report/', views.morning_report, name='morning_report'),
    path('portal/pendency/', views.pendency_report, name='pendency_report'),
    path('portal/pendency/observations/<int:pk>/',
         views.pendency_observations, name='pendency_observations'),
    path('portal/prev-month-update/', views.prev_month_update, name='prev_month_update'),
    path('portal/result/<int:pk>/', views.tool_result, name='tool_result'),
    path('portal/btpl/', views.btpl_sheet, name='btpl_sheet'),
    path('portal/btpl/api/', views.btpl_api, name='btpl_api'),
    path('portal/btpl/download/', views.btpl_download, name='btpl_download'),
    path('portal/btpl/settings/', views.btpl_settings, name='btpl_settings'),
    path('portal/ftl/', views.ftl_sheet, name='ftl_sheet'),
    path('portal/ftl/api/', views.ftl_api, name='ftl_api'),
    path('portal/ftl/download/', views.ftl_download, name='ftl_download'),
    path('portal/ftl/settings/', views.ftl_settings, name='ftl_settings'),
    path('portal/attendance/', views.attendance_sheet, name='attendance_sheet'),
    path('portal/attendance/download/', views.attendance_download, name='attendance_download'),
    path('portal/attendance/settings/', views.attendance_settings, name='attendance_settings'),
]
