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

    # COF
    path('portal/cof/', views.cof_generator, name='cof_generator'),
    path('portal/cof/workbook/', views.cof_workbook, name='cof_workbook'),
    path('portal/cof/workbook/download/', views.cof_workbook_download, name='cof_workbook_download'),
    path('portal/cof/success/<int:pk>/', views.cof_success, name='cof_success'),
    path('portal/cof/history/', views.cof_history, name='cof_history'),
    path('portal/download/<int:file_id>/', views.download_file, name='download_file'),

    path('portal/morning-report/', views.morning_report, name='morning_report'),
    path('portal/pendency/', views.pendency_report, name='pendency_report'),
]
