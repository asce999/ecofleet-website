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
    path('portal/cof/', views.cof_generator, name='cof_generator'),
    path('portal/morning-report/', views.morning_report, name='morning_report'),
    path('portal/pendency/', views.pendency_report, name='pendency_report'),
]