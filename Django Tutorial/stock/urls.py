from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

app_name = "stock"
urlpatterns = [
    path("", views.index, name="index"),
]
urlpatterns += staticfiles_urlpatterns()