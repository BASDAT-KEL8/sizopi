from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
from accounts.models import StafAdmin, Pengunjung

# Dummy data for attractions
DUMMY_ATTRACTIONS = [
    {
        'nama': 'Pertunjukan lumba-lumba',
        'lokasi': 'Area Akuatik',
        'jam': '10:00',
        'kapasitas': 50
    },
    {
        'nama': 'Feeding time harimau',
        'lokasi': 'Area Karnivora',
        'jam': '14:00',
        'kapasitas': 30
    },
    {
        'nama': 'Pertunjukan gajah',
        'lokasi': 'Area Mamalia',
        'jam': '13:00',
        'kapasitas': 40
    }
]

# Dummy data for reservations
DUMMY_RESERVATIONS = [
    {
        'id': 1,
        'username_pengunjung': 'Arif',
        'nama_atraksi': 'Pertunjukan lumba-lumba',
        'tanggal_reservasi': '2025-05-12',
        'jumlah_tiket': 10,
        'status': 'Terjadwal'
    },
    {
        'id': 2,
        'username_pengunjung': 'Winnie',
        'nama_atraksi': 'Feeding time harimau',
        'tanggal_reservasi': '2025-05-11',
        'jumlah_tiket': 3,
        'status': 'Dibatalkan'
    },
    {
        'id': 3,
        'username_pengunjung': 'Budi',
        'nama_atraksi': 'Pertunjukan gajah',
        'tanggal_reservasi': '2025-05-15',
        'jumlah_tiket': 5,
        'status': 'Terjadwal'
    },
    {
        'id': 4,
        'username_pengunjung': 'Sarah',
        'nama_atraksi': 'Pertunjukan lumba-lumba',
        'tanggal_reservasi': '2025-05-13',
        'jumlah_tiket': 4,
        'status': 'Terjadwal'
    },
    {
        'id': 5,
        'username_pengunjung': 'John',
        'nama_atraksi': 'Feeding time harimau',
        'tanggal_reservasi': '2025-05-14',
        'jumlah_tiket': 2,
        'status': 'Terjadwal'
    }
]

def index(request):
    # Get username from session
    username = request.session.get('username')
    
    # Check user role using proper model queries
    if StafAdmin.objects.filter(username_sa=username).exists():
        context = {
            'reservations': DUMMY_RESERVATIONS,
            'is_staff': True
        }
    elif Pengunjung.objects.filter(username_p=username).exists():
        # For regular users, filter their own reservations
        user_reservations = [r for r in DUMMY_RESERVATIONS if r['username_pengunjung'] == username]
        context = {
            'reservations': user_reservations,
            'is_staff': False
        }
    else:
        # Handle case where user role is not found
        messages.error(request, 'User role not found')
        return redirect('login')
        
    return render(request, 'booking/index.html', context)

def create_reservation(request):
    username = request.session.get('username')
    # Block staff admin from creating reservations using proper model query
    if StafAdmin.objects.filter(username_sa=username).exists():
        messages.error(request, 'Staff admin tidak diizinkan membuat reservasi')
        return redirect('booking_index')
        
    if request.method == 'POST':
        nama_atraksi = request.POST.get('nama_atraksi')
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))
        
        # Validate booking
        attraction = next((a for a in DUMMY_ATTRACTIONS if a['nama'] == nama_atraksi), None)
        if attraction and jumlah_tiket <= attraction['kapasitas']:
            messages.success(request, 'Reservasi berhasil dibuat!')
        else:
            messages.error(request, 'Reservasi gagal: Kapasitas tidak mencukupi')
        
        return render(request, 'booking/detail_reservation.html', {
            'nama_atraksi': nama_atraksi,
            'lokasi': attraction['lokasi'] if attraction else '',
            'jam': attraction['jam'] if attraction else '',
            'tanggal': tanggal,
            'jumlah_tiket': jumlah_tiket,
            'status': 'Terjadwal'
        })
    
    context = {
        'attractions': DUMMY_ATTRACTIONS
    }
    return render(request, 'booking/create_reservation.html', context)

def edit_reservation(request, id):
    # Find reservation in dummy data
    reservation = next((r for r in DUMMY_RESERVATIONS if r['id'] == id), None)
    
    if request.method == 'POST':
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))
        
        messages.success(request, 'Reservasi berhasil diperbarui!')
        return render(request, 'booking/detail_reservation.html', {
            'nama_atraksi': reservation['nama_atraksi'],
            'lokasi': next((a['lokasi'] for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), ''),
            'jam': next((a['jam'] for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), ''),
            'tanggal': tanggal,
            'jumlah_tiket': jumlah_tiket,
            'status': 'Terjadwal'
        })
    
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        return render(request, 'booking/index.html')
        
    context = {
        'reservation': reservation,
        'attraction': next((a for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), None)
    }
    return render(request, 'booking/edit_reservation.html', context)

def cancel_reservation(request, id):
    # Find reservation in dummy data
    reservation = next((r for r in DUMMY_RESERVATIONS if r['id'] == id), None)
    
    if request.method == 'POST':
        messages.success(request, 'Reservasi berhasil dibatalkan')
        return redirect('booking_index')
    
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        return redirect('booking_index')
        
    context = {
        'reservation': reservation,
        'attraction': next((a for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), None)
    }
    return render(request, 'booking/cancel_reservation.html', context)

def detail_reservation(request, id):
    # Find reservation in dummy data
    reservation = next((r for r in DUMMY_RESERVATIONS if r['id'] == id), None)
    
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        return redirect('booking_index')
        
    attraction = next((a for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), None)
    
    context = {
        'nama_atraksi': reservation['nama_atraksi'],
        'lokasi': attraction['lokasi'] if attraction else '',
        'jam': attraction['jam'] if attraction else '',
        'tanggal': reservation['tanggal_reservasi'],
        'jumlah_tiket': reservation['jumlah_tiket'],
        'status': reservation['status']
    }
    return render(request, 'booking/detail_reservation.html', context)
