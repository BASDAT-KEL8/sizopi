from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import StafAdmin, Pengunjung

# Dummy data untuk semua atraksi
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

# Dummy data global: staff lihat semua, pengunjung hanya yang cocok username-nya
DUMMY_RESERVATIONS = [
    # data lama
    {
        'id': 1,
        'username_pengunjung': 'joshuapengunjung',
        'nama_atraksi': 'Pertunjukan lumba-lumba',
        'tanggal_reservasi': '2025-05-12',
        'jumlah_tiket': 10,
        'status': 'Terjadwal'
    },
    {
        'id': 2,
        'username_pengunjung': 'joshuapengunjung',
        'nama_atraksi': 'Feeding time harimau',
        'tanggal_reservasi': '2025-05-11',
        'jumlah_tiket': 3,
        'status': 'Dibatalkan'
    },
    {
        'id': 3,
        'username_pengunjung': 'joshuapengunjung',
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
    },
    # dua contoh tambahan: ganti 'alice' / 'bob' sesuai username test-mu
    {
        'id': 6,
        'username_pengunjung': 'alice',
        'nama_atraksi': 'Pertunjukan gajah',
        'tanggal_reservasi': '2025-06-01',
        'jumlah_tiket': 3,
        'status': 'Terjadwal'
    },
    {
        'id': 7,
        'username_pengunjung': 'bob',
        'nama_atraksi': 'Feeding time harimau',
        'tanggal_reservasi': '2025-06-02',
        'jumlah_tiket': 1,
        'status': 'Terjadwal'
    },
]

def index(request):
    username = request.session.get('username')
    
    # Staff melihat semua
    if StafAdmin.objects.filter(username_sa=username).exists():
        context = {
            'reservations': DUMMY_RESERVATIONS,
            'is_staff': True
        }
    # Pengunjung hanya yang match username-nya (case-insensitive)
    elif Pengunjung.objects.filter(username_p=username).exists():
        user_reservations = [
            r for r in DUMMY_RESERVATIONS
            if r['username_pengunjung'].lower() == username.lower()
        ]
        context = {
            'reservations': user_reservations,
            'is_staff': False
        }
    else:
        messages.error(request, 'User role not found')
        return redirect('login')
        
    return render(request, 'booking/index.html', context)

def create_reservation(request):
    username = request.session.get('username')
    if StafAdmin.objects.filter(username_sa=username).exists():
        messages.error(request, 'Staff admin tidak diizinkan membuat reservasi')
        return redirect('booking_index')
        
    if request.method == 'POST':
        nama_atraksi = request.POST.get('nama_atraksi')
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))
        
        attraction = next((a for a in DUMMY_ATTRACTIONS if a['nama'] == nama_atraksi), None)
        if attraction and jumlah_tiket <= attraction['kapasitas']:
            messages.success(request, 'Reservasi berhasil dibuat!')
            status = 'Terjadwal'
        else:
            messages.error(request, 'Reservasi gagal: Kapasitas tidak mencukupi')
            status = 'Gagal'
        
        return render(request, 'booking/detail_reservation.html', {
            'nama_atraksi': nama_atraksi,
            'lokasi': attraction['lokasi'] if attraction else '',
            'jam': attraction['jam'] if attraction else '',
            'tanggal': tanggal,
            'jumlah_tiket': jumlah_tiket,
            'status': status
        })
    
    return render(request, 'booking/create_reservation.html', {
        'attractions': DUMMY_ATTRACTIONS
    })

def edit_reservation(request, id):
    reservation = next((r for r in DUMMY_RESERVATIONS if r['id'] == id), None)
    
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        return redirect('booking_index')
        
    if request.method == 'POST':
        nama_atraksi = request.POST.get('nama_atraksi')
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))
        
        # Find the selected attraction
        attraction = next((a for a in DUMMY_ATTRACTIONS if a['nama'] == nama_atraksi), None)
        
        # Validate capacity
        if attraction and jumlah_tiket <= attraction['kapasitas']:
            messages.success(request, 'Reservasi berhasil diperbarui!')
            return redirect('detail_reservation', id=id)
        else:
            messages.error(request, 'Update gagal: Kapasitas tidak mencukupi')
    
    return render(request, 'booking/edit_reservation.html', {
        'reservation': reservation,
        'attractions': DUMMY_ATTRACTIONS,
        'attraction': next((a for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), None),
        'nama_atraksi': reservation['nama_atraksi']  # Add this line
    })

def cancel_reservation(request, id):
    reservation = next((r for r in DUMMY_RESERVATIONS if r['id'] == id), None)
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        return redirect('booking_index')
    
    if request.method == 'POST':
        messages.success(request, 'Reservasi berhasil dibatalkan')
        return redirect('booking_index')
    
    return render(request, 'booking/cancel_reservation.html', {
        'reservation': reservation,
        'attraction': next((a for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), None)
    })

def detail_reservation(request, id):
    all_res = DUMMY_RESERVATIONS
    reservation = next((r for r in all_res if r['id'] == id), None)
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        return redirect('booking_index')
        
    attraction = next((a for a in DUMMY_ATTRACTIONS if a['nama'] == reservation['nama_atraksi']), None)
    
    return render(request, 'booking/detail_reservation.html', {
        'id': id,  # Add this line
        'nama_atraksi': reservation['nama_atraksi'],
        'lokasi': attraction['lokasi'] if attraction else '',
        'jam': attraction['jam'] if attraction else '',
        'tanggal': reservation['tanggal_reservasi'],
        'jumlah_tiket': reservation['jumlah_tiket'],
        'status': reservation['status']
    })
