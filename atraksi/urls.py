from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.manage_atraksi, name='manage_atraksi'),
    path('tambah/', views.tambah_atraksi, name='tambah_atraksi'),
    path('edit/<str:nama_atraksi>/', views.edit_atraksi, name='edit_atraksi'),
    path('hapus/<str:nama_atraksi>/', views.hapus_atraksi, name='hapus_atraksi'),
    path('wahana/tambah/', views.tambah_wahana, name='tambah_wahana'),
    path('wahana/edit/<str:nama_wahana>/', views.edit_wahana, name='edit_wahana'),
    path('wahana/hapus/<str:nama_wahana>/', views.hapus_wahana, name='hapus_wahana'),
]
