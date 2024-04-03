from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

app_name = "single_page_app"
urlpatterns = [
    path("", views.index, name="index"),
    path("help/", views.help_page, name="help"),
    path("about/", views.about_page, name="about"),
    path("service/", views.service_page, name="service"),
    path("data/", views.data_page, name="data"),
]
urlpatterns += staticfiles_urlpatterns()
