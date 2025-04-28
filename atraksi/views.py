from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Fasilitas, Atraksi, Wahana
from datetime import datetime

def manage_atraksi(request):
    if 'email' not in request.session:
        return redirect('login')
    
    # Check if user is staff admin - need to check based on StafAdmin model
    username = request.session.get('username')
    from accounts.models import StafAdmin
    
    if not StafAdmin.objects.filter(username_sa=username).exists():
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini')
        return redirect('dashboard')
        
    atraksi_list = Atraksi.objects.select_related('nama_atraksi').all()
    wahana_list = Wahana.objects.select_related('nama_wahana').all()
    
    context = {
        'atraksi_list': atraksi_list,
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
        hewan = request.POST.getlist('hewan')

        # Create Fasilitas first
        fasilitas = Fasilitas.objects.create(
            nama=nama,
            jadwal=jadwal,
            kapasitas_max=kapasitas
        )
        
        # Create Atraksi
        Atraksi.objects.create(
            nama_atraksi=fasilitas,
            lokasi=lokasi
        )
        
        messages.success(request, 'Atraksi berhasil ditambahkan')
        return redirect('manage_atraksi')
        
    return render(request, 'atraksi/tambah_atraksi.html')

def edit_atraksi(request, nama_atraksi):
    atraksi = Atraksi.objects.select_related('nama_atraksi').get(nama_atraksi=nama_atraksi)
    
    if request.method == 'POST':
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        
        # Update Fasilitas
        atraksi.nama_atraksi.jadwal = jadwal
        atraksi.nama_atraksi.kapasitas_max = kapasitas
        atraksi.nama_atraksi.save()
        
        messages.success(request, 'Atraksi berhasil diperbarui')
        return redirect('manage_atraksi')
        
    context = {'atraksi': atraksi}
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
