# urls.py
from django.urls import path
from . import views

app_name = 'adopsi'

urlpatterns = [
    # Halaman publik
    path('', views.home, name='home'),
    path('daftar-hewan/', views.list_hewan, name='list_hewan'),
    path('hewan/<uuid:hewan_id>/', views.detail_hewan, name='detail_hewan'),
    
    # Halaman pengunjung/adopter
    # path('hewan/<uuid:hewan_id>/adopt/', views.adopt_hewan, name='adopt_hewan'),
    path('dashboard/', views.dashboard_adopter, name='dashboard_adopter'),
    # path('adopsi/<int:adopsi_id>/', views.detail_adopsi, name='detail_adopsi'),
    # path('adopsi/<int:adopsi_id>/perpanjang/', views.perpanjang_adopsi, name='perpanjang_adopsi'),
    # path('adopsi/<int:adopsi_id>/berhenti/', views.berhenti_adopsi, name='berhenti_adopsi'),

    path("adopsi/<uuid:adopsi_id>/sertifikat/", views.sertifikat_adopsi, name="sertifikat_adopsi"),
    
    # Halaman admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/daftar-hewan/', views.admin_daftar_hewan, name='admin_daftar_hewan'),
    # path('admin/daftar-adopsi/', views.admin_daftar_adopsi, name='admin_daftar_adopsi'),
    path('admin/daftar-adopter/', views.admin_daftar_adopter, name='admin_daftar_adopter'),
    path('admin/adopter/<uuid:adopter_id>/', views.admin_detail_adopter, name='admin_detail_adopter'),
    
    # path('admin/adopsi/<str:adopsi_id>/', views.admin_detail_adopsi, name='admin_detail_adopsi'),
    # path('adopsi/<str:adopsi_id>/berhenti/', views.berhenti_adopsi, name='berhenti_adopsi'),

    # path('admin/adopsi/<int:adopsi_id>/payment/', views.admin_update_payment, name='admin_update_payment'),

    path('admin/hewan/<uuid:hewan_id>/proses-adopsi/', views.admin_proses_adopsi, name='admin_proses_adopsi'),


    path('admin/detail_adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.admin_detail_adopsi, name='admin_detail_adopsi'),

    path('admin/update_payment/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.admin_update_payment, name='admin_update_payment'),
    path('admin/berhenti_adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.berhenti_adopsi, name='berhenti_adopsi'),


    path('api/verify-user/', views.verify_username, name='verify_username'),


]