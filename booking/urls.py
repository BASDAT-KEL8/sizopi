from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='booking_index'),
    path('create/', views.create_reservation, name='create_reservation'),
    path('edit/<int:id>/', views.edit_reservation, name='edit_reservation'),
    path('cancel/<int:id>/', views.cancel_reservation, name='cancel_reservation'),
]
