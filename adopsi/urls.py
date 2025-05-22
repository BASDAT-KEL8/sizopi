from django.urls import path
from . import views

app_name = 'adopsi'

urlpatterns = [
    # ========== USER/ADOPTER PAGES ==========
    path('dashboard/', views.dashboard_adopter, name='dashboard_adopter'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.detail_adopsi, name='detail_adopsi'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/perpanjang/', views.perpanjang_adopsi, name='perpanjang_adopsi'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/laporan/', views.laporan_kondisi, name='laporan_kondisi'),
    path('adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/sertifikat/', views.sertifikat_adopsi, name='sertifikat_adopsi'),
    
    # ========== GENERAL PAGES ==========
    path('hewan/<uuid:hewan_id>/', views.detail_hewan, name='detail_hewan'),
    
    # ========== ADMIN DASHBOARD ==========
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # ========== ADMIN DATA MANAGEMENT ==========
    path('admin/daftar-hewan/', views.admin_daftar_hewan, name='admin_daftar_hewan'),
    path('admin/daftar-adopter/', views.admin_daftar_adopter, name='admin_daftar_adopter'),
    
    # ========== ADMIN ADOPTER MANAGEMENT ==========
    # Detail adopter - with optional type parameter for better routing
    path('admin/adopter/<uuid:adopter_id>/', views.admin_detail_adopter, name='admin_detail_adopter'),
    path('admin/adopter/<uuid:adopter_id>/<str:adopter_type>/', views.admin_detail_adopter, name='admin_detail_adopter_typed'),
    
    # Delete adopter - FIXED: Single URL pattern with proper parameters
    path('admin/hapus-adopter/<uuid:adopter_id>/<str:adopter_type>/', views.admin_hapus_adopter, name='admin_hapus_adopter'),
    
    # ========== ADMIN ADOPTION MANAGEMENT ==========
    # Process new adoption
    path('admin/hewan/<uuid:hewan_id>/proses-adopsi/', views.admin_proses_adopsi, name='admin_proses_adopsi'),
    
    # Adoption details and actions
    path('admin/detail_adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.admin_detail_adopsi, name='admin_detail_adopsi'),
    path('admin/update_payment/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.admin_update_payment, name='admin_update_payment'),
    
    # Stop/End adoption
    path('admin/berhenti_adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.berhenti_adopsi, name='berhenti_adopsi'),
    
    # Delete adoption record
    path('admin/hapus-adopsi/<uuid:id_adopter>/<uuid:id_hewan>/<str:tgl_mulai_adopsi>/', views.admin_hapus_adopsi, name='admin_hapus_adopsi'),
    
    # ========== API ENDPOINTS ==========
    path('api/verify-user/', views.verify_username, name='verify_username'),
]

