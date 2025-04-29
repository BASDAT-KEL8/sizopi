# urls.py
from django.urls import path
from . import views

app_name = 'adopsi'

urlpatterns = [

    path('dashboard/', views.dashboard_adopter, name='dashboard_adopter'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.detail_adopsi, name='detail_adopsi'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/perpanjang/', views.perpanjang_adopsi, name='perpanjang_adopsi'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/laporan/', views.laporan_kondisi, name='laporan_kondisi'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/sertifikat/', views.sertifikat_adopsi, name='sertifikat_adopsi'),
    
    # page admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/daftar-hewan/', views.admin_daftar_hewan, name='admin_daftar_hewan'),
    path('admin/daftar-adopter/', views.admin_daftar_adopter, name='admin_daftar_adopter'),
    path('admin/adopter/<uuid:adopter_id>/', views.admin_detail_adopter, name='admin_detail_adopter'),
    path('hewan/<uuid:hewan_id>/', views.detail_hewan, name='detail_hewan'),
   
    
    path('admin/hewan/<uuid:hewan_id>/proses-adopsi/', views.admin_proses_adopsi, name='admin_proses_adopsi'),
    path('admin/adopter/<int:adopter_id>/hapus/', views.admin_hapus_adopter, name='admin_hapus_adopter'),
    path('admin/detail_adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.admin_detail_adopsi, name='admin_detail_adopsi'),
    path('admin/update_payment/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.admin_update_payment, name='admin_update_payment'),
    path('admin/berhenti_adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.berhenti_adopsi, name='berhenti_adopsi'),
    path('api/verify-user/', views.verify_username, name='verify_username'),
]