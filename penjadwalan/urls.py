from django.urls import path
from . import views

app_name = 'penjadwalan'

urlpatterns = [
    path('jadwal-pemeriksaan/', views.list_jadwal_pemeriksaan, name='list_jadwal_pemeriksaan'),
    path('jadwal-pemeriksaan/<uuid:id_hewan>/tambah/', views.tambah_jadwal_pemeriksaan, name='tambah_jadwal_pemeriksaan'),
    path('jadwal-pemeriksaan/<uuid:id_hewan>/<str:jadwal_id>/edit/', views.edit_jadwal_pemeriksaan, name='edit_jadwal_pemeriksaan'),
    path('jadwal-pemeriksaan/<uuid:id_hewan>/edit-frekuensi/', views.edit_frekuensi_pemeriksaan, name='edit_frekuensi_pemeriksaan'),
    path('jadwal-pemeriksaan/<uuid:id_hewan>/<str:jadwal_id>/hapus/', views.hapus_jadwal_pemeriksaan, name='hapus_jadwal_pemeriksaan'),
]
