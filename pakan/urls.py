from django.urls import path
from . import views

app_name = 'pakan'

urlpatterns = [
    path('', views.list_hewan_pakan, name='list_hewan_pakan'),
    path('hewan/<uuid:id_hewan>/pakan/', views.list_pemberian_pakan, name='list_pemberian_pakan'),
    path('hewan/<uuid:id_hewan>/pakan/tambah/', views.tambah_jadwal_pakan, name='tambah_jadwal_pakan'),
    path('hewan/<uuid:id_hewan>/pakan/<str:jadwal>/edit/', views.edit_pemberian_pakan, name='edit_pemberian_pakan'),
    path('hewan/<uuid:id_hewan>/pakan/<str:jadwal>/hapus/', views.hapus_pemberian_pakan, name='hapus_pemberian_pakan'),
    path('hewan/<uuid:id_hewan>/pakan/<str:jadwal>/beri/', views.beri_pakan, name='beri_pakan'),
    path('riwayat-pemberian-pakan/', views.riwayat_pemberian_pakan, name='riwayat_pemberian_pakan'),
]