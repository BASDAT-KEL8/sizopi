from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='booking_index'),
    path('create/', views.create_reservation, name='create_reservation'),
    path('edit/<str:id>/', views.edit_reservation, name='edit_reservation'),
    path('cancel/<str:id>/', views.cancel_reservation, name='cancel_reservation'),
    path('detail/<str:id>/', views.detail_reservation, name='detail_reservation'),
]