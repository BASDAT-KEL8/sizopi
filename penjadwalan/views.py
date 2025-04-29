from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

from accounts.models import DokterHewan


# Dummy data for animals
dummy_hewan_list = [
    {
        'id': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),
        'nama': 'Simba',
        'spesies': 'Singa Afrika',
        'asal_hewan': 'Kenya',
        'tanggal_lahir': '2020-01-15',
        'habitat': 'Savanna',
        'status_kesehatan': 'Sehat',
        'freq_pemeriksaan_rutin': 3  # Pemeriksaan setiap 3 bulan
    },
    {
        'id': uuid.UUID('a7c52d8e-3f10-4d92-9e3b-6c8a90b23d45'),
        'nama': 'Leo',
        'spesies': 'Singa Afrika',
        'asal_hewan': 'Tanzania',
        'tanggal_lahir': '2019-06-20',
        'habitat': 'Savanna',
        'status_kesehatan': 'Sehat',
        'freq_pemeriksaan_rutin': 2  # Pemeriksaan setiap 2 bulan
    },
    {
        'id': uuid.UUID('b9d63f1a-5e22-4c83-af4b-7d9b12c34e67'),
        'nama': 'Raja',
        'spesies': 'Harimau Sumatera',
        'asal_hewan': 'Indonesia',
        'tanggal_lahir': '2021-03-10',
        'habitat': 'Hutan Tropis',
        'status_kesehatan': 'Sehat',
        'freq_pemeriksaan_rutin': 4  # Pemeriksaan setiap 4 bulan
    }
]

# Dummy data for health examination schedules
dummy_jadwal_list = [
    {
        'id': '1',
        'id_hewan': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),  # Simba
        'tgl_pemeriksaan_selanjutnya': timezone.now() + timedelta(days=30),
    },
    {
        'id': '2',
        'id_hewan': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),  # Simba
        'tgl_pemeriksaan_selanjutnya': timezone.now() + timedelta(days=60),
    },
    {
        'id': '3',
        'id_hewan': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),  # Simba
        'tgl_pemeriksaan_selanjutnya': timezone.now() + timedelta(days=90),
    },
    {
        'id': '4',
        'id_hewan': uuid.UUID('a7c52d8e-3f10-4d92-9e3b-6c8a90b23d45'),  # Leo
        'tgl_pemeriksaan_selanjutnya': timezone.now() + timedelta(days=15),
    },
    {
        'id': '5',
        'id_hewan': uuid.UUID('a7c52d8e-3f10-4d92-9e3b-6c8a90b23d45'),  # Leo
        'tgl_pemeriksaan_selanjutnya': timezone.now() + timedelta(days=45),
    },
    {
        'id': '6',
        'id_hewan': uuid.UUID('b9d63f1a-5e22-4c83-af4b-7d9b12c34e67'),  # Raja
        'tgl_pemeriksaan_selanjutnya': timezone.now() + timedelta(days=45),
    }
]


def check_dokter_hewan(view_func):
    def wrapper(request, *args, **kwargs):
        username = request.session.get('username')
        if not username:
            messages.error(request, 'Silakan login terlebih dahulu')
            return redirect('login')
            
        # Check if user is a dokter hewan
        if not DokterHewan.objects.filter(username_dh__username=username).exists():
            messages.error(request, 'Anda tidak memiliki akses ke halaman ini')
            return redirect('dashboard')
            
        return view_func(request, *args, **kwargs)
    return wrapper

@check_dokter_hewan
def list_jadwal_pemeriksaan(request):
    """Menampilkan daftar jadwal pemeriksaan kesehatan hewan"""
    context = {
        'hewan_list': dummy_hewan_list,
        'jadwal_list': dummy_jadwal_list
    }
    return render(request, 'penjadwalan/list_jadwal_pemeriksaan.html', context)

@check_dokter_hewan
def tambah_jadwal_pemeriksaan(request, id_hewan):
    """Menambah jadwal pemeriksaan kesehatan untuk hewan tertentu"""
    hewan = next((h for h in dummy_hewan_list if h['id'] == id_hewan), None)
    
    if request.method == 'POST':
        messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil ditambahkan')
        return redirect('penjadwalan:list_jadwal_pemeriksaan')
    
    return render(request, 'penjadwalan/tambah_jadwal.html', {'hewan': hewan})

@check_dokter_hewan
def edit_jadwal_pemeriksaan(request, id_hewan, jadwal_id):
    """Mengedit jadwal pemeriksaan kesehatan"""
    jadwal = next((j for j in dummy_jadwal_list if j['id'] == jadwal_id), None)
    hewan = next((h for h in dummy_hewan_list if h['id'] == id_hewan), None)
    
    if request.method == 'POST':
        messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil diperbarui')
        return redirect('penjadwalan:list_jadwal_pemeriksaan')
    
    return render(request, 'penjadwalan/edit_jadwal.html', {
        'jadwal': jadwal,
        'hewan': hewan
    })

@check_dokter_hewan
def edit_frekuensi_pemeriksaan(request, id_hewan):
    """Mengedit frekuensi pemeriksaan rutin"""
    hewan = next((h for h in dummy_hewan_list if h['id'] == id_hewan), None)
    
    if request.method == 'POST':
        # In a real implementation, we would update the frequency in the database here
        messages.success(request, 'Frekuensi pemeriksaan rutin berhasil diperbarui')
        return redirect('penjadwalan:list_jadwal_pemeriksaan')
    
    return render(request, 'penjadwalan/edit_frekuensi.html', {
        'hewan': hewan
    })

@check_dokter_hewan
def hapus_jadwal_pemeriksaan(request, id_hewan, jadwal_id):
    """Menghapus jadwal pemeriksaan kesehatan"""
    jadwal = next((j for j in dummy_jadwal_list if j['id'] == jadwal_id), None)
    hewan = next((h for h in dummy_hewan_list if h['id'] == id_hewan), None)
    
    if request.method == 'POST':
        messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil dihapus')
        return redirect('penjadwalan:list_jadwal_pemeriksaan')
    
    return render(request, 'penjadwalan/hapus_jadwal.html', {
        'jadwal': jadwal,
        'hewan': hewan
    })
