from django.contrib import admin
from django.urls import path, include
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

app_name = "stock"
urlpatterns = [
    path("", views.index, name="index"),
    path('download-stocks/', views.download_stock_list, name='download-stocks'),
    path('buy/', views.charts, name="charts"),
    path('sell/', views.sellStocks, name="sell"),
]
urlpatterns += staticfiles_urlpatterns()