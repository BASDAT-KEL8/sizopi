from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Fasilitas, Atraksi, Wahana
from datetime import datetime

def manage_atraksi(request):
    if 'email' not in request.session:
        return redirect('login')
    
    # Check if user is staff admin
    username = request.session.get('username')
    from accounts.models import StafAdmin
    
    if not StafAdmin.objects.filter(username_sa=username).exists():
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini')
        return redirect('dashboard')
        
    atraksi_list = Atraksi.objects.select_related('nama_atraksi').all()
    wahana_list = Wahana.objects.select_related('nama_wahana').all()
    
    # Get participating animals and assigned trainers for each attraction
    from .models import Berpartisipasi
    from penjadwalan.models import JadwalPenugasan
    from accounts.models import PelatihHewan, Pengguna
    from datetime import datetime
    
    atraksi_dengan_detail = []
    for atraksi in atraksi_list:
        # Get participating animals
        hewan_berpartisipasi = Berpartisipasi.objects.select_related('id_hewan').filter(
            nama_fasilitas=atraksi.nama_atraksi
        )
        
        # Get assigned trainer for the nearest schedule
        jadwal_pelatih = JadwalPenugasan.objects.select_related(
            'username_lh__username_lh'
        ).filter(
            nama_atraksi=atraksi,
            tgl_penugasan__gte=datetime.now()
        ).order_by('tgl_penugasan').first()
        
        pelatih = None
        if jadwal_pelatih:
            pengguna = jadwal_pelatih.username_lh.username_lh
            pelatih = {
                'nama': f"{pengguna.nama_depan} {pengguna.nama_belakang}",
                'jadwal': jadwal_pelatih.tgl_penugasan
            }
        
        atraksi_dengan_detail.append({
            'atraksi': atraksi,
            'hewan_list': hewan_berpartisipasi,
            'pelatih': pelatih
        })
    
    context = {
        'atraksi_list': atraksi_dengan_detail,
        'wahana_list': wahana_list
    }
    return render(request, 'atraksi/manage.html', context)

def tambah_atraksi(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        lokasi = request.POST.get('lokasi')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        pelatih = request.POST.get('pelatih')
        hewan_list = request.POST.getlist('hewan')
        jadwal_pelatih = request.POST.get('jadwal_pelatih')

        # Create Fasilitas first
        fasilitas = Fasilitas.objects.create(
            nama=nama,
            jadwal=jadwal,
            kapasitas_max=kapasitas
        )
        
        # Create Atraksi
        atraksi = Atraksi.objects.create(
            nama_atraksi=fasilitas,
            lokasi=lokasi
        )

        # Create Berpartisipasi entries for selected animals
        from .models import Berpartisipasi
        from satwa.models import Hewan
        
        for hewan_id in hewan_list:
            hewan = Hewan.objects.get(id=hewan_id)
            Berpartisipasi.objects.create(
                nama_fasilitas=fasilitas,
                id_hewan=hewan
            )

        # Create JadwalPenugasan for the trainer
        if pelatih and jadwal_pelatih:
            from penjadwalan.models import JadwalPenugasan
            from accounts.models import PelatihHewan
            
            pelatih_obj = PelatihHewan.objects.get(username_lh=pelatih)
            JadwalPenugasan.objects.create(
                username_lh=pelatih_obj,
                tgl_penugasan=jadwal_pelatih,
                nama_atraksi=atraksi
            )
        
        messages.success(request, 'Atraksi berhasil ditambahkan')
        return redirect('manage_atraksi')
    
    # Get data for the form
    from accounts.models import PelatihHewan, Pengguna
    from satwa.models import Hewan
    
    pelatih_list = PelatihHewan.objects.select_related('username_lh').all()
    hewan_list = Hewan.objects.all()
    
    context = {
        'pelatih_list': pelatih_list,
        'hewan_list': hewan_list,
    }
    return render(request, 'atraksi/tambah_atraksi.html', context)

def edit_atraksi(request, nama_atraksi):
    atraksi = Atraksi.objects.select_related('nama_atraksi').get(nama_atraksi=nama_atraksi)
    
    if request.method == 'POST':
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        pelatih = request.POST.get('pelatih')
        jadwal_pelatih = request.POST.get('jadwal_pelatih')
        hewan_list = request.POST.getlist('hewan')
        
        # Update Fasilitas
        atraksi.nama_atraksi.jadwal = jadwal
        atraksi.nama_atraksi.kapasitas_max = kapasitas
        atraksi.nama_atraksi.save()

        # Update participating animals
        from .models import Berpartisipasi
        from satwa.models import Hewan
        
        # Remove existing participations
        Berpartisipasi.objects.filter(nama_fasilitas=atraksi.nama_atraksi).delete()
        
        # Add new participations
        for hewan_id in hewan_list:
            hewan = Hewan.objects.get(id=hewan_id)
            Berpartisipasi.objects.create(
                nama_fasilitas=atraksi.nama_atraksi,
                id_hewan=hewan
            )

        # Update trainer schedule
        from penjadwalan.models import JadwalPenugasan
        from accounts.models import PelatihHewan
        
        # Remove existing schedule
        JadwalPenugasan.objects.filter(nama_atraksi=atraksi).delete()
        
        # Add new schedule if trainer is selected
        if pelatih and jadwal_pelatih:
            pelatih_obj = PelatihHewan.objects.get(username_lh=pelatih)
            JadwalPenugasan.objects.create(
                username_lh=pelatih_obj,
                tgl_penugasan=jadwal_pelatih,
                nama_atraksi=atraksi
            )
        
        messages.success(request, 'Atraksi berhasil diperbarui')
        return redirect('manage_atraksi')

    # Get current data
    from .models import Berpartisipasi
    from accounts.models import PelatihHewan, Pengguna
    from satwa.models import Hewan
    from penjadwalan.models import JadwalPenugasan
    
    current_animals = Berpartisipasi.objects.filter(
        nama_fasilitas=atraksi.nama_atraksi
    ).select_related('id_hewan')
    
    current_schedule = JadwalPenugasan.objects.filter(
        nama_atraksi=atraksi
    ).select_related('username_lh__username_lh').first()
    
    pelatih_list = PelatihHewan.objects.select_related('username_lh').all()
    hewan_list = Hewan.objects.all()
    
    context = {
        'atraksi': atraksi,
        'pelatih_list': pelatih_list,
        'hewan_list': hewan_list,
        'current_animals': current_animals,
        'current_schedule': current_schedule,
    }
    return render(request, 'atraksi/edit_atraksi.html', context)

def hapus_atraksi(request, nama_atraksi):
    if request.method == 'POST':
        atraksi = Atraksi.objects.get(nama_atraksi=nama_atraksi)
        atraksi.delete()
        messages.success(request, 'Atraksi berhasil dihapus')
        return redirect('manage_atraksi')
    
    return render(request, 'atraksi/hapus_atraksi.html', {'nama_atraksi': nama_atraksi})

# Similar functions for Wahana
def tambah_wahana(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        peraturan = request.POST.get('peraturan')

        # Create Fasilitas first
        fasilitas = Fasilitas.objects.create(
            nama=nama,
            jadwal=jadwal,
            kapasitas_max=kapasitas
        )
        
        # Create Wahana
        Wahana.objects.create(
            nama_wahana=fasilitas,
            peraturan=peraturan
        )
        
        messages.success(request, 'Wahana berhasil ditambahkan')
        return redirect('manage_atraksi')
        
    return render(request, 'atraksi/tambah_wahana.html')

def edit_wahana(request, nama_wahana):
    wahana = Wahana.objects.select_related('nama_wahana').get(nama_wahana=nama_wahana)
    
    if request.method == 'POST':
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        peraturan = request.POST.get('peraturan')
        
        # Update Fasilitas
        wahana.nama_wahana.jadwal = jadwal
        wahana.nama_wahana.kapasitas_max = kapasitas
        wahana.nama_wahana.save()
        
        # Update Wahana
        wahana.peraturan = peraturan
        wahana.save()
        
        messages.success(request, 'Wahana berhasil diperbarui')
        return redirect('manage_atraksi')
        
    context = {'wahana': wahana}
    return render(request, 'atraksi/edit_wahana.html', context)

def hapus_wahana(request, nama_wahana):
    if request.method == 'POST':
        wahana = Wahana.objects.get(nama_wahana=nama_wahana)
        wahana.delete()
        messages.success(request, 'Wahana berhasil dihapus')
        return redirect('manage_atraksi')
    
    return render(request, 'atraksi/hapus_wahana.html', {'nama_wahana': nama_wahana})
