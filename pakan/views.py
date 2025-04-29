from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

# Dummy data for animals
dummy_hewan_list = [
    {
        'id': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),
        'nama': 'Simba',
        'spesies': 'Singa Afrika',
        'asal_hewan': 'Kenya',
        'tanggal_lahir': '2020-01-15',
        'habitat': 'Savanna',
        'status_kesehatan': 'Sehat'
    },
    {
        'id': uuid.UUID('a7c52d8e-3f10-4d92-9e3b-6c8a90b23d45'),
        'nama': 'Leo',
        'spesies': 'Singa Afrika',
        'asal_hewan': 'Tanzania',
        'tanggal_lahir': '2019-06-20',
        'habitat': 'Savanna',
        'status_kesehatan': 'Sehat'
    },
    {
        'id': uuid.UUID('b9d63f1a-5e22-4c83-af4b-7d9b12c34e67'),
        'nama': 'Raja',
        'spesies': 'Harimau Sumatera',
        'asal_hewan': 'Indonesia',
        'tanggal_lahir': '2021-03-10',
        'habitat': 'Hutan Tropis',
        'status_kesehatan': 'Sehat'
    },
    {
        'id': uuid.UUID('c8e74f2b-6f33-5d94-bf5c-8e0c23d45f78'),
        'nama': 'Gajah Kecil',
        'spesies': 'Gajah Sumatera',
        'asal_hewan': 'Indonesia',
        'tanggal_lahir': '2022-05-15',
        'habitat': 'Hutan Tropis',
        'status_kesehatan': 'Sehat'
    },
    {
        'id': uuid.UUID('d9f85a3c-7a44-6e05-cf6d-9f1d34e56a89'),
        'nama': 'Koko',
        'spesies': 'Orangutan',
        'asal_hewan': 'Kalimantan',
        'tanggal_lahir': '2018-08-22',
        'habitat': 'Hutan Hujan',
        'status_kesehatan': 'Dalam Perawatan'
    }
]

# Dummy data for feeding schedules
dummy_pakan_list = [
    {
        'id': '1',
        'id_hewan': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),
        'jenis': 'Daging Sapi',
        'jumlah': 5000,
        'jadwal': timezone.now(),
        'status': 'Menunggu Pemberian'
    },
    {
        'id': '2',
        'id_hewan': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),
        'jenis': 'Daging Ayam',
        'jumlah': 3000,
        'jadwal': timezone.now() + timedelta(days=1),
        'status': 'Menunggu Pemberian'
    },
    {
        'id': '3',
        'id_hewan': uuid.UUID('96f41ce7-8bc9-4c81-8dbb-9f1240602aa4'),
        'jenis': 'Daging Kambing',
        'jumlah': 4000,
        'jadwal': timezone.now() - timedelta(days=1),
        'status': 'Selesai Diberikan'
    }
]

# Dummy data for feeding history
dummy_riwayat_pakan = [
    {
        'hewan': {
            'nama': 'Simba',
            'spesies': 'Singa Afrika',
            'asal_hewan': 'Kenya',
            'tanggal_lahir': '2020-01-15',
            'habitat': 'Savanna', 
            'status_kesehatan': 'Sehat'
        },
        'jenis': 'Daging Sapi',
        'jumlah': 5000,
        'jadwal': timezone.now() - timedelta(days=1),
        'status': 'Selesai Diberikan'
    },
    {
        'hewan': {
            'nama': 'Leo',
            'spesies': 'Singa Afrika',
            'asal_hewan': 'Tanzania',
            'tanggal_lahir': '2019-06-20',
            'habitat': 'Savanna',
            'status_kesehatan': 'Sehat'
        },
        'jenis': 'Daging Kambing',
        'jumlah': 4000,
        'jadwal': timezone.now() - timedelta(days=2),
        'status': 'Selesai Diberikan'
    },
    {
        'hewan': {
            'nama': 'Raja',
            'spesies': 'Harimau Sumatera',
            'asal_hewan': 'Indonesia',
            'tanggal_lahir': '2021-03-10',
            'habitat': 'Hutan Tropis',
            'status_kesehatan': 'Sehat'
        },
        'jenis': 'Daging Ayam',
        'jumlah': 3000,
        'jadwal': timezone.now() - timedelta(days=3),
        'status': 'Selesai Diberikan'
    },
    {
        'hewan': {
            'nama': 'Gajah Kecil',
            'spesies': 'Gajah Sumatera',
            'asal_hewan': 'Indonesia',
            'tanggal_lahir': '2022-05-15',
            'habitat': 'Hutan Tropis',
            'status_kesehatan': 'Sehat'
        },
        'jenis': 'Rumput Segar',
        'jumlah': 15000,
        'jadwal': timezone.now() - timedelta(days=1),
        'status': 'Selesai Diberikan'
    },
    {
        'hewan': {
            'nama': 'Koko',
            'spesies': 'Orangutan',
            'asal_hewan': 'Kalimantan',
            'tanggal_lahir': '2018-08-22',
            'habitat': 'Hutan Hujan',
            'status_kesehatan': 'Dalam Perawatan'
        },
        'jenis': 'Buah-buahan',
        'jumlah': 2000,
        'jadwal': timezone.now() - timedelta(days=1),
        'status': 'Selesai Diberikan'
    }
]

def list_pemberian_pakan(request, id_hewan):
    """
    View function for listing feeding schedules for a specific animal
    id_hewan is already a UUID object from URL routing
    """
    hewan = next((h for h in dummy_hewan_list if h['id'] == id_hewan), None)
    context = {
        'hewan': hewan,
        'pakan_list': [p for p in dummy_pakan_list if p['id_hewan'] == id_hewan]
    }
    return render(request, 'pakan/list_pemberian_pakan.html', context)

def tambah_jadwal_pakan(request, id_hewan):
    if request.method == 'POST':
        messages.success(request, 'Jadwal pemberian pakan berhasil ditambahkan')
        return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
    return render(request, 'pakan/tambah_pakan.html', {'id_hewan': id_hewan})

def edit_pemberian_pakan(request, id_hewan, pakan_id):
    pakan = next((item for item in dummy_pakan_list if item['id'] == pakan_id), None)
    if request.method == 'POST':
        messages.success(request, 'Jadwal pemberian pakan berhasil diperbarui')
        return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
    return render(request, 'pakan/edit_pakan.html', {
        'pakan': pakan,
        'id_hewan': id_hewan  # Pass id_hewan separately
    })

def hapus_pemberian_pakan(request, id_hewan, pakan_id):
    pakan = next((item for item in dummy_pakan_list if item['id'] == pakan_id), None)
    if request.method == 'POST':
        messages.success(request, 'Data pemberian pakan berhasil dihapus')
        return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
    return render(request, 'pakan/hapus_pakan.html', {
        'pakan': pakan,
        'id_hewan': id_hewan  # Pass id_hewan separately
    })

def beri_pakan(request, id_hewan, pakan_id):
    """Mark a feeding schedule as completed"""
    pakan = next((item for item in dummy_pakan_list if item['id'] == pakan_id), None)
    if pakan and pakan['status'] == 'Menunggu Pemberian':
        pakan['status'] = 'Selesai Diberikan'
        messages.success(request, 'Pemberian pakan berhasil dicatat')
    return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)

def riwayat_pemberian_pakan(request):
    """
    Menampilkan riwayat pemberian pakan yang dilakukan oleh penjaga hewan yang sedang login
    """
    context = {
        'riwayat_pakan': dummy_riwayat_pakan
    }
    return render(request, 'pakan/riwayat_pemberian_pakan.html', context)
