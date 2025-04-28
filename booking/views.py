from django.shortcuts import render
from django.contrib import messages
from datetime import datetime

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
    }
]

# Dummy data for reservations
DUMMY_RESERVATIONS = [
    {
        'username_pengunjung': 'Arif',
        'nama_atraksi': 'Pertunjukan lumba-lumba',
        'tanggal_reservasi': '2025-05-12',
        'jumlah_tiket': 10,
        'status': 'Terjadwal'
    },
    {
        'username_pengunjung': 'Winnie',
        'nama_atraksi': 'Feeding time harimau',
        'tanggal_reservasi': '2025-05-11',
        'jumlah_tiket': 3,
        'status': 'Dibatalkan'
    }
]

def index(request):
    # Get username from session
    username = request.session.get('username')
    
    # Filter reservations for current user if logged in
    user_reservations = []
    if username:
        user_reservations = [r for r in DUMMY_RESERVATIONS if r['username_pengunjung'] == username]
    
    context = {
        'reservations': user_reservations
    }
    return render(request, 'booking/index.html', context)

def create_reservation(request):
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
    reservation = next((r for r in DUMMY_RESERVATIONS if r['username_pengunjung'] == request.session.get('username')), None)
    
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
    if request.method == 'POST':
        messages.success(request, 'Reservasi berhasil dibatalkan')
        return render(request, 'booking/index.html')
    
    # Find reservation in dummy data
    reservation = next((r for r in DUMMY_RESERVATIONS if r['username_pengunjung'] == request.session.get('username')), None)
    
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        return render(request, 'booking/index.html')
        
    context = {
        'reservation': reservation,
        'attraction': next((a for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), None)
    }
    return render(request, 'booking/cancel_reservation.html', context)
