from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.choose_role_view, name='choose_role'),  # Pilih role dulu
    path('register/pengunjung/', views.register_pengunjung_view, name='register_pengunjung'),
    path('register/dokter/', views.register_dokter_view, name='register_dokter'),
    path('register/staff/', views.register_staff_view, name='register_staff'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('', lambda request: redirect('/accounts/login/')),

]