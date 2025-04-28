from django.urls import path
from . import views

app_name = 'rekam_medis'

urlpatterns = [
    path('', views.list_rekam_medis, name='list_rekam_medis'),
    path('tambah/', views.tambah_rekam_medis, name='tambah_rekam_medis'),
    path('edit/<uuid:id_hewan>/<str:tanggal_pemeriksaan>/', views.edit_rekam_medis, name='edit_rekam_medis'),
    path('hapus/<uuid:id_hewan>/<str:tanggal_pemeriksaan>/', views.hapus_rekam_medis, name='hapus_rekam_medis'),
]
