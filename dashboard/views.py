from django.shortcuts import render, redirect
from django.db.models import Count, Sum
from datetime import date, datetime, timedelta
from accounts.models import Pengguna, DokterHewan, PenjagaHewan, Spesialisasi, StafAdmin, PelatihHewan, Pengunjung
from rekam_medis.models import CatatanMedis
from penjadwalan.models import JadwalPenugasan
from atraksi.models import Atraksi, Berpartisipasi

def dashboard_view(request):
    if 'email' not in request.session:
        return redirect('login')
    
    context = {}
    username = request.session.get('username')
    
    # Add current time to context
    context['now'] = datetime.now()
    
    # Get basic user info
    user = Pengguna.objects.get(username=username)
    context['nama_lengkap'] = f"{user.nama_depan} {user.nama_tengah or ''} {user.nama_belakang}".strip()
    context['username'] = user.username
    context['email'] = user.email
    context['no_telepon'] = user.no_telepon
    
    # Current date for dummy data
    today = date.today()
    
    # Check user role and get role-specific info
    if DokterHewan.objects.filter(username_dh=username).exists():
        context['role'] = 'Dokter Hewan'
        dokter = DokterHewan.objects.get(username_dh=username)
        context['no_str'] = dokter.no_str
        
        # # Get real specialization data from database
        # spesialisasi = Spesialisasi.objects.filter(username_sh=username).values_list('nama_spesialisasi', flat=True)
        # context['spesialisasi'] = list(spesialisasi)

        # Dummy data for specialization
        context['spesialisasi'] = ['Mamalia Besar', 'Reptil']
        
        # Count handled medical records
        context['jumlah_hewan_ditangani'] = CatatanMedis.objects.filter(username_dh=username).count()
    
    elif PenjagaHewan.objects.filter(username_jh=username).exists():
        context['role'] = 'Penjaga Hewan'
        penjaga = PenjagaHewan.objects.get(username_jh=username)
        context['id_staf'] = penjaga.id_staf
        # Dummy data for animals fed
        context['jumlah_hewan_diberi_pakan'] = 15
    
    elif StafAdmin.objects.filter(username_sa=username).exists():
        context['role'] = 'Staf Administrasi'
        admin = StafAdmin.objects.get(username_sa=username)
        context['id_staf'] = admin.id_staf
        
        # Dummy data for admin
        context['penjualan_tiket_hari_ini'] = 2500000
        context['jumlah_pengunjung_hari_ini'] = 50
        context['pendapatan_mingguan'] = 15000000
    
    elif PelatihHewan.objects.filter(username_lh=username).exists():
        context['role'] = 'Staf Pelatih Pertunjukan'
        pelatih = PelatihHewan.objects.get(username_lh=username)
        context['id_staf'] = pelatih.id_staf
        
        # Dummy data for shows
        context['jadwal_hari_ini'] = [
            {
                'tgl_penugasan': datetime.now().replace(hour=10, minute=0),
                'nama_atraksi': {'nama': 'Pertunjukan Lumba-lumba'},
                'status': 'Selesai'
            },
            {
                'tgl_penugasan': datetime.now().replace(hour=14, minute=30),
                'nama_atraksi': {'nama': 'Pertunjukan Gajah'},
                'status': 'Akan Datang'
            }
        ]
        
        # Dummy data for trained animals
        context['hewan_dilatih'] = [
            {
                'id_hewan': {'nama': 'Dumbo', 'spesies': 'Gajah Asia'},
                'status_latihan': 'Siap Tampil'
            },
            {
                'id_hewan': {'nama': 'Flipper', 'spesies': 'Lumba-lumba Hidung Botol'},
                'status_latihan': 'Dalam Pelatihan'
            }
        ]
    
    elif Pengunjung.objects.filter(username_p=username).exists():
        context['role'] = 'Pengunjung'
        pengunjung = Pengunjung.objects.get(username_p=username)
        context['alamat'] = pengunjung.alamat
        context['tanggal_lahir'] = pengunjung.tgl_lahir
        
        # Dummy data for visit history
        context['riwayat_kunjungan'] = [
            {
                'tanggal_pembelian': today - timedelta(days=30),
                'no_tiket': 'TK-001',
                'is_used': True,
                'status': 'Terpakai'
            },
            {
                'tanggal_pembelian': today - timedelta(days=15),
                'no_tiket': 'TK-002',
                'is_used': True,
                'status': 'Terpakai'
            }
        ]
        
        # Dummy data for active tickets
        context['tiket'] = [
            {
                'no_tiket': 'TK-003',
                'tanggal_pembelian': today,
                'is_used': False,
                'status': 'Belum Digunakan'
            },
            {
                'no_tiket': 'TK-004',
                'tanggal_pembelian': today + timedelta(days=5),
                'is_used': False,
                'status': 'Belum Digunakan'
            }
        ]

    return render(request, 'dashboard/dashboard.html', context)






