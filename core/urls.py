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
]