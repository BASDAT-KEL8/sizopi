from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import (
    Adopsi, Adopter, Individu, Organisasi
)
from rekam_medis.models import CatatanMedis
from accounts.models import (Pengunjung, Pengguna, StafAdmin)
from satwa.models import Hewan
from .forms import AdopsiForm, PerpanjangAdopsiForm

def home(request):
    """Halaman utama program adopsi"""
    return render(request, 'adopsi/home.html')

def list_hewan(request):
    """Menampilkan daftar hewan yang tersedia untuk diadopsi"""
    animals = Hewan.objects.all().order_by('nama')
    
    # Ambil ID hewan yang sedang diadopsi (tanggal akhir adopsi > hari ini)
    adopted_animal_ids = Adopsi.objects.filter(
        tgl_berhenti_adopsi__gt=timezone.now().date()
    ).values_list('id_hewan', flat=True)
    
    # Filter berdasarkan status adopsi
    status_filter = request.GET.get('status', None)
    if status_filter == 'diadopsi':
        animals = animals.filter(id__in=adopted_animal_ids)
    elif status_filter == 'available':
        animals = animals.exclude(id__in=adopted_animal_ids)
    
    # Filter berdasarkan spesies
    species_filter = request.GET.get('species', None)
    if species_filter:
        animals = animals.filter(spesies__icontains=species_filter)
    
    # Pagination
    paginator = Paginator(animals, 12)  # 12 hewan per halaman
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Tambahkan status adopsi ke setiap objek hewan
    for animal in page_obj:
        animal.is_adopted = animal.id in adopted_animal_ids
    
    context = {
        'animals': page_obj,
        'status_filter': status_filter,
        'species_filter': species_filter,
        'distinct_species': Hewan.objects.values_list('spesies', flat=True).distinct(),
    }
    return render(request, 'adopsi/list_hewan.html', context)

def detail_hewan(request, hewan_id):
    """Menampilkan detail hewan dan status adopsinya"""
    hewan = get_object_or_404(Hewan, id=hewan_id)
    
    # Cek status adopsi
    current_adoption = Adopsi.objects.filter(
        id_hewan=hewan,
        tgl_berhenti_adopsi__gt=timezone.now().date()
    ).first()
    
    # Ambil catatan medis hewan
    medical_records = CatatanMedis.objects.filter(id_hewan=hewan).order_by('-tanggal_pemeriksaan')
    
    context = {
        'hewan': hewan,
        'current_adoption': current_adoption,
        'medical_records': medical_records,
    }
    return render(request, 'adopsi/detail_hewan.html', context)

# @login_required
def adopt_hewan(request, hewan_id):
    """Form pendaftaran adopsi hewan"""
    hewan = get_object_or_404(Hewan, id=hewan_id)
    
    # Cek apakah hewan sudah diadopsi
    is_adopted = Adopsi.objects.filter(
        id_hewan=hewan,
        tgl_berhenti_adopsi__gt=timezone.now().date()
    ).exists()
    
    if is_adopted:
        messages.error(request, f"Hewan ini sudah diadopsi oleh orang lain.")
        return redirect('adopsi:detail_hewan', hewan_id=hewan_id)
    
    # Cek apakah user sudah punya akun Pengunjung
    try:
        pengunjung = Pengunjung.objects.get(username_p=request.user.username)
    except Pengunjung.DoesNotExist:
        messages.error(request, "Anda harus memiliki akun pengunjung untuk mengadopsi hewan.")
        return redirect('profile_update')
    
    if request.method == 'POST':
        form = AdopsiForm(request.POST)
        if form.is_valid():
            # Cek atau buat Adopter
            try:
                adopter = Adopter.objects.get(username_adopter=pengunjung)
            except Adopter.DoesNotExist:
                adopter = Adopter.objects.create(
                    username_adopter=pengunjung,
                    id_adopter=uuid.uuid4(),  # Generate UUID
                    total_kontribusi=0
                )
            
            # Proses tipe adopter (individu atau organisasi)
            adopter_type = form.cleaned_data['adopter_type']
            if adopter_type == 'individu':
                # Simpan data individu
                try:
                    individu = Individu.objects.get(id_adopter=adopter)
                    individu.nama = form.cleaned_data['nama']
                    individu.nik = form.cleaned_data['nik']
                    individu.save()
                except Individu.DoesNotExist:
                    individu = Individu.objects.create(
                        id_adopter=adopter,
                        nik=form.cleaned_data['nik'],
                        nama=form.cleaned_data['nama'],
                    )
            else:
                # Simpan data organisasi
                try:
                    organisasi = Organisasi.objects.get(id_adopter=adopter)
                    organisasi.nama_organisasi = form.cleaned_data['nama']
                    organisasi.npp = form.cleaned_data['npp']
                    organisasi.save()
                except Organisasi.DoesNotExist:
                    organisasi = Organisasi.objects.create(
                        id_adopter=adopter,
                        npp=form.cleaned_data['npp'],
                        nama_organisasi=form.cleaned_data['nama'],
                    )
            
            # Hitung tanggal akhir adopsi
            tgl_mulai = timezone.now().date()
            periode_bulan = form.cleaned_data['periode']
            tgl_akhir = tgl_mulai + timedelta(days=30 * periode_bulan)
            
            # Simpan data adopsi
            adopsi = Adopsi.objects.create(
                id_adopter=adopter,
                id_hewan=hewan,
                status_pembayaran='tertunda',
                tgl_mulai_adopsi=tgl_mulai,
                tgl_berhenti_adopsi=tgl_akhir,
                kontribusi_finansial=form.cleaned_data['kontribusi']
            )
            
            # Update total kontribusi adopter
            adopter.total_kontribusi += form.cleaned_data['kontribusi']
            adopter.save()
            
            messages.success(request, f"Terima kasih! Anda telah berhasil mengadopsi {hewan.nama}.")
            return redirect('adopsi:detail_adopsi', adopsi_id=adopsi.id)
    else:
        form = AdopsiForm(initial={'kontribusi': 500000, 'periode': 3})
    
    context = {
        'hewan': hewan,
        'form': form,
    }
    return render(request, 'adopsi/adopt_form.html', context)

# @login_required
def dashboard_adopter(request):
    """Dashboard untuk pengunjung yang menjadi adopter"""
   
    pengunjung = Pengunjung.objects.get(username_p=request.user.username)
    adopter = Adopter.objects.get(username_adopter=pengunjung)
    # except (Pengunjung.DoesNotExist, Adopter.DoesNotExist):
    #     messages.error(request, "Anda belum terdaftar sebagai adopter.")
    #     return redirect('adopsi:list_hewan')
    
    # Dapatkan semua adopsi yang dilakukan oleh adopter
    adopsi_list = Adopsi.objects.filter(id_adopter=adopter).order_by('-tgl_mulai_adopsi')
    
    # Dapatkan informasi hewan yang diadopsi
    adoptions_with_animals = []
    for adopsi in adopsi_list:
        is_active = adopsi.tgl_berhenti_adopsi >= timezone.now().date()
        adoptions_with_animals.append({
            'adopsi': adopsi,
            'hewan': adopsi.id_hewan,
            'is_active': is_active
        })
    
    context = {
        'adopter': adopter,
        'adoptions': adoptions_with_animals,
    }
    return render(request, 'adopsi/dashboard_adopter.html', context)

# @login_required
def detail_adopsi(request, adopsi_id):
    """Menampilkan detail adopsi tertentu"""
    # For testing only, we'll use a simple get first to debug
    adopsi = get_object_or_404(Adopsi, pk=adopsi_id)
    
    # Ambil catatan medis hewan setelah tanggal adopsi
    medical_records = CatatanMedis.objects.filter(
        id_hewan=adopsi.id_hewan,
        tanggal_pemeriksaan__gte=adopsi.tgl_mulai_adopsi
    ).order_by('-tanggal_pemeriksaan')
    
    context = {
        'adopsi': adopsi,
        'hewan': adopsi.id_hewan,
        'medical_records': medical_records,
    }
    return render(request, 'adopsi/detail_adopsi.html', context)

# @login_required
def perpanjang_adopsi(request, adopsi_id):
    """Form perpanjangan adopsi hewan"""
    # For testing only, we'll use a simple get
    adopsi = get_object_or_404(Adopsi, pk=adopsi_id)
    
    if request.method == 'POST':
        form = PerpanjangAdopsiForm(request.POST)
        if form.is_valid():
            # Hitung tanggal akhir adopsi baru
            periode_bulan = form.cleaned_data['periode']
            tgl_akhir_baru = adopsi.tgl_berhenti_adopsi + timedelta(days=30 * periode_bulan)
            
            # Update data adopsi
            adopsi.tgl_berhenti_adopsi = tgl_akhir_baru
            adopsi.kontribusi_finansial += form.cleaned_data['kontribusi']
            adopsi.status_pembayaran = 'tertunda'
            adopsi.save()
            
            # Update total kontribusi adopter
            adopter = adopsi.id_adopter  # Get adopter from the adoption
            adopter.total_kontribusi += form.cleaned_data['kontribusi']
            adopter.save()
            
            messages.success(request, f"Adopsi {adopsi.id_hewan.nama} berhasil diperpanjang hingga {tgl_akhir_baru.strftime('%d %B %Y')}.")
            return redirect('adopsi:detail_adopsi', adopsi_id=adopsi.id)
    else:
        form = PerpanjangAdopsiForm(initial={'kontribusi': 500000, 'periode': 3})
    
    context = {
        'adopsi': adopsi,
        'hewan': adopsi.id_hewan,
        'form': form,
    }
    return render(request, 'adopsi/perpanjang_form.html', context)

# @login_required
def berhenti_adopsi(request, adopsi_id):
    """Konfirmasi penghentian adopsi hewan"""
    # Get the adoption by ID
    adopsi = get_object_or_404(Adopsi, pk=adopsi_id)
    
    # Check if user is admin
    is_admin = False
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
        is_admin = True
    except:
        pass

    if request.method == 'POST':
        # End the adoption
        adopsi.tgl_berhenti_adopsi = timezone.now().date()
        adopsi.save()
        
        messages.success(request, f"Adopsi {adopsi.id_hewan.nama} telah dihentikan.")
        
        if is_admin:
            return redirect('adopsi:admin_daftar_adopsi')
        else:
            return redirect('adopsi:dashboard_adopter')
    
    context = {
        'adopsi': adopsi,
        'hewan': adopsi.id_hewan,
    }
    return render(request, 'adopsi/berhenti_adopsi.html', context)

# Admin views
# @login_required
def admin_dashboard(request):
    """Dashboard untuk admin program adopsi"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    # Statistics for the dashboard
    total_animals = Hewan.objects.count()
    total_adopters = Adopter.objects.count()
    active_adoptions = Adopsi.objects.filter(
        tgl_berhenti_adopsi__gt=timezone.now().date()
    ).count()
    pending_payments = Adopsi.objects.filter(status_pembayaran='tertunda').count()
    
    # Get top adopters by total_kontribusi - no annotate needed
    top_adopters = Adopter.objects.order_by('-total_kontribusi')[:5]
    
    # Enrich top adopters with type info and manually count adoptions
    for adopter in top_adopters:
        try:
            individu = Individu.objects.get(id_adopter=adopter)
            adopter.type = 'individu'
            adopter.individu = individu
        except Individu.DoesNotExist:
            try:
                organisasi = Organisasi.objects.get(id_adopter=adopter)
                adopter.type = 'organisasi'
                adopter.organisasi = organisasi
            except Organisasi.DoesNotExist:
                adopter.type = 'unknown'
        
        # Manually count adoptions for this adopter
        # Use .filter() instead of trying to count with SQL directly
        adopter.adopsi_count = Adopsi.objects.filter(id_adopter=adopter).count()
    
    # Recent adoptions
    recent_adoptions = Adopsi.objects.all().order_by('-tgl_mulai_adopsi')[:5]
    
    context = {
        'total_animals': total_animals,
        'total_adopters': total_adopters,
        'active_adoptions': active_adoptions,
        'pending_payments': pending_payments,
        'top_adopters': top_adopters,
        'recent_adoptions': recent_adoptions,
        'now': timezone.now(),
    }
    return render(request, 'adopsi/admin_dashboard.html', context)

# @login_required
def admin_daftar_hewan(request):
    """Menampilkan daftar hewan untuk admin"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    animals = Hewan.objects.all().order_by('nama')
    
    # Get adopted animal IDs
    adopted_animal_ids = Adopsi.objects.filter(
        tgl_berhenti_adopsi__gt=timezone.now().date()
    ).values_list('id_hewan', flat=True)
    
    # Filter berdasarkan status adopsi
    status_filter = request.GET.get('status', None)
    if status_filter == 'diadopsi':
        animals = animals.filter(id__in=adopted_animal_ids)
    elif status_filter == 'available':
        animals = animals.exclude(id__in=adopted_animal_ids)
    
    # Filter berdasarkan spesies
    species_filter = request.GET.get('species', None)
    if species_filter:
        animals = animals.filter(spesies__icontains=species_filter)
    
    # Pagination
    paginator = Paginator(animals, 12)  # 12 hewan per halaman
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'animals': page_obj,
        'status_filter': status_filter,
        'species_filter': species_filter,
        'distinct_species': Hewan.objects.values_list('spesies', flat=True).distinct(),
        'adopted_animal_ids': adopted_animal_ids,
    }
    return render(request, 'adopsi/admin/daftar_hewan.html', context)

# @login_required
def admin_daftar_adopsi(request):
    """Menampilkan daftar adopsi untuk admin"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    adoptions = Adopsi.objects.all().order_by('-tgl_mulai_adopsi')
    
    # Filter berdasarkan status adopsi
    status_filter = request.GET.get('status', None)
    if status_filter == 'active':
        adoptions = adoptions.filter(tgl_berhenti_adopsi__gt=timezone.now().date())
    elif status_filter == 'ended':
        adoptions = adoptions.filter(tgl_berhenti_adopsi__lte=timezone.now().date())
    
    # Filter berdasarkan status pembayaran
    payment_filter = request.GET.get('payment', None)
    if payment_filter:
        adoptions = adoptions.filter(status_pembayaran=payment_filter)
    
    # Pagination
    paginator = Paginator(adoptions, 15)  # 15 adopsi per halaman
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'adoptions': page_obj,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'now': timezone.now(),
    }
    return render(request, 'adopsi/admin/daftar_adopsi.html', context)

# @login_required
def admin_daftar_adopter(request):
    """Menampilkan daftar adopter untuk admin"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    adopters = Adopter.objects.all().order_by('-total_kontribusi')
    
    # Add type info to adopters
    for adopter in adopters:
        if Individu.objects.filter(id_adopter=adopter).exists():
            adopter.type = 'individu'
        elif Organisasi.objects.filter(id_adopter=adopter).exists():
            adopter.type = 'organisasi'
        else:
            adopter.type = 'unknown'
    
    # Search by name
    search_query = request.GET.get('search', None)
    if search_query:
        # Find matching individuals and organizations
        individu_adopters = Individu.objects.filter(
            nama__icontains=search_query
        ).values_list('id_adopter', flat=True)
        
        organisasi_adopters = Organisasi.objects.filter(
            nama_organisasi__icontains=search_query
        ).values_list('id_adopter', flat=True)
        
        # Combine search results
        adopter_ids = list(individu_adopters) + list(organisasi_adopters)
        adopters = [adopter for adopter in adopters if adopter.id_adopter in adopter_ids]
    
    # Pagination
    paginator = Paginator(adopters, 15)  # 15 adopter per halaman
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'adopters': page_obj,
        'search_query': search_query,
    }
    return render(request, 'adopsi/admin/daftar_adopter.html', context)

# @login_required
def admin_detail_adopter(request, adopter_id):
    """Menampilkan detail adopter untuk admin"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    adopter = get_object_or_404(Adopter, id_adopter=adopter_id)
    
    # Check the adopter type (individual or organization)
    try:
        individu = Individu.objects.get(id_adopter=adopter)
        adopter_type = 'individu'
        adopter_detail = individu
    except Individu.DoesNotExist:
        try:
            organisasi = Organisasi.objects.get(id_adopter=adopter)
            adopter_type = 'organisasi'
            adopter_detail = organisasi
        except Organisasi.DoesNotExist:
            adopter_type = 'unknown'
            adopter_detail = None
    
    # Get adoption history
    adoptions = Adopsi.objects.filter(id_adopter=adopter).order_by('-tgl_mulai_adopsi')
    
    context = {
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung': adopter.username_adopter,
        'adoptions': adoptions,
        'now': timezone.now(),
    }
    return render(request, 'adopsi/admin/detail_adopter.html', context)

# @login_required
def admin_update_payment(request, adopsi_id):
    """Update status pembayaran adopsi oleh admin"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    # Get the adoption by ID
    adopsi = get_object_or_404(Adopsi, pk=adopsi_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status_pembayaran')
        if new_status in ['tertunda', 'lunas']:
            adopsi.status_pembayaran = new_status
            adopsi.save()
            messages.success(request, f"Status pembayaran adopsi telah diperbarui menjadi '{new_status}'.")
        else:
            messages.error(request, "Status pembayaran tidak valid.")
        
        return redirect('adopsi:admin_detail_adopsi', adopsi_id=adopsi.id)
    
    context = {
        'adopsi': adopsi,
        'hewan': adopsi.id_hewan,
    }
    return render(request, 'adopsi/admin/update_payment.html', context)

# @login_required
def admin_detail_adopsi(request, adopsi_id):
    """Menampilkan detail adopsi untuk admin"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    # Get the adoption by ID
    adopsi = get_object_or_404(Adopsi, pk=adopsi_id)
    
    # Get adopter details
    adopter = adopsi.id_adopter
    
    # Check adopter type
    try:
        individu = Individu.objects.get(id_adopter=adopter)
        adopter_type = 'individu'
        adopter_detail = individu
    except Individu.DoesNotExist:
        try:
            organisasi = Organisasi.objects.get(id_adopter=adopter)
            adopter_type = 'organisasi'
            adopter_detail = organisasi
        except Organisasi.DoesNotExist:
            adopter_type = 'unknown'
            adopter_detail = None
    
    # Get medical records after adoption start date
    medical_records = CatatanMedis.objects.filter(
        id_hewan=adopsi.id_hewan,
        tanggal_pemeriksaan__gte=adopsi.tgl_mulai_adopsi
    ).order_by('-tanggal_pemeriksaan')
    
    context = {
        'adopsi': adopsi,
        'hewan': adopsi.id_hewan,
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung': adopter.username_adopter,
        'medical_records': medical_records,
        'now': timezone.now(),
    }
    return render(request, 'adopsi/admin/detail_adopsi.html', context)

def admin_hapus_adopter(request, adopter_id):
    """Menghapus data adopter"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    adopter = get_object_or_404(Adopter, id_adopter=adopter_id)
    
    if request.method == 'POST':
        # Delete associated data
        try:
            # First end all active adoptions
            active_adoptions = Adopsi.objects.filter(
                id_adopter=adopter,
                tgl_berhenti_adopsi__gt=timezone.now().date()
            )
            for adoption in active_adoptions:
                adoption.tgl_berhenti_adopsi = timezone.now().date()
                adoption.save()
            
            # Delete individu or organisasi data
            Individu.objects.filter(id_adopter=adopter).delete()
            Organisasi.objects.filter(id_adopter=adopter).delete()
            
            # Finally delete the adopter
            adopter.delete()
            
            messages.success(request, "Data adopter berhasil dihapus.")
            return redirect('adopsi:admin_daftar_adopter')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {str(e)}")
    
    context = {
        'adopter': adopter,
    }
    return render(request, 'adopsi/admin/hapus_adopter.html', context)

def admin_proses_adopsi(request, hewan_id):
    """Form pendaftaran adopsi hewan oleh admin"""
    # Check if user is admin
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass  # For development, allow all access
    
    hewan = get_object_or_404(Hewan, id=hewan_id)
    
    # Cek apakah hewan sudah diadopsi
    is_adopted = Adopsi.objects.filter(
        id_hewan=hewan,
        tgl_berhenti_adopsi__gt=timezone.now().date()
    ).exists()
    
    if is_adopted:
        messages.error(request, f"Hewan ini sudah diadopsi oleh orang lain.")
        return redirect('adopsi:admin_daftar_hewan')
    
    if request.method == 'POST':
        # Get username from form
        username = request.POST.get('username')
        
        try:
            pengunjung = Pengunjung.objects.get(username_p=username)
        except Pengunjung.DoesNotExist:
            messages.error(request, "Akun pengunjung tidak ditemukan.")
            return redirect('adopsi:admin_proses_adopsi', hewan_id=hewan_id)
        
        # Cek atau buat Adopter
        try:
            adopter = Adopter.objects.get(username_adopter=pengunjung)
        except Adopter.DoesNotExist:
            adopter = Adopter.objects.create(
                username_adopter=pengunjung,
                id_adopter=uuid.uuid4(),
                total_kontribusi=0
            )
        
        # Proses tipe adopter
        adopter_type = request.POST.get('adopter_type')
        
        if adopter_type == 'individu':
            # Get form values for individu
            nik = request.POST.get('nik')
            nama = request.POST.get('nama')
            
            # Simpan data individu
            try:
                individu = Individu.objects.get(id_adopter=adopter)
                individu.nik = nik
                individu.nama = nama
                individu.save()
            except Individu.DoesNotExist:
                individu = Individu.objects.create(
                    id_adopter=adopter,
                    nik=nik,
                    nama=nama
                )
            
            # Update pengunjung data if provided
            alamat = request.POST.get('alamat')
            if alamat:
                pengunjung.alamat = alamat
                pengunjung.save()
            
            kontribusi = int(request.POST.get('kontribusi', 500000))
            periode = int(request.POST.get('periode', 3))
            status_pembayaran = request.POST.get('status_pembayaran', 'tertunda')
            
        else:  # organisasi
            # Get form values for organisasi
            npp = request.POST.get('npp')
            nama_organisasi = request.POST.get('nama_organisasi')
            
            # Simpan data organisasi
            try:
                organisasi = Organisasi.objects.get(id_adopter=adopter)
                organisasi.npp = npp
                organisasi.nama_organisasi = nama_organisasi
                organisasi.save()
            except Organisasi.DoesNotExist:
                organisasi = Organisasi.objects.create(
                    id_adopter=adopter,
                    npp=npp,
                    nama_organisasi=nama_organisasi
                )
            
            # Update pengunjung data if provided
            alamat = request.POST.get('alamat_organisasi')
            if alamat:
                pengunjung.alamat = alamat
                # Update pengunjung data if provided
            alamat = request.POST.get('alamat_organisasi')
            if alamat:
                pengunjung.alamat = alamat
                pengunjung.save()
            
            kontribusi = int(request.POST.get('kontribusi_organisasi', 500000))
            periode = int(request.POST.get('periode_organisasi', 3))
            status_pembayaran = request.POST.get('status_pembayaran_organisasi', 'tertunda')
        
        # Hitung tanggal akhir adopsi
        tgl_mulai = timezone.now().date()
        tgl_akhir = tgl_mulai + timedelta(days=30 * periode)
        
        # Simpan data adopsi
        adopsi = Adopsi.objects.create(
            id_adopter=adopter,
            id_hewan=hewan,
            status_pembayaran=status_pembayaran,
            tgl_mulai_adopsi=tgl_mulai,
            tgl_berhenti_adopsi=tgl_akhir,
            kontribusi_finansial=kontribusi
        )
        
        # Update total kontribusi adopter
        adopter.total_kontribusi += kontribusi
        adopter.save()
        
        messages.success(request, f"Adopsi berhasil didaftarkan untuk {hewan.nama}.")
        return redirect('adopsi:admin_detail_adopsi', adopsi_id=adopsi.id)
    
    context = {
        'hewan': hewan,
    }
    return render(request, 'adopsi/admin/proses_adopsi.html', context)

# API for verifying username
def verify_username(request):
    """API untuk verifikasi username pengunjung"""
    username = request.GET.get('username', '')
    
    try:
        # Find the user
        pengguna = Pengguna.objects.get(username=username)
        # Check if user has a pengunjung account
        try:
            pengunjung = Pengunjung.objects.get(username_p=pengguna)
            
            # Check if user is already an adopter
            try:
                adopter = Adopter.objects.get(username_adopter=pengunjung)
                
                # Get adopter details
                try:
                    individu = Individu.objects.get(id_adopter=adopter)
                    adopter_info = {
                        'type': 'individu',
                        'nama': individu.nama,
                        'nik': individu.nik
                    }
                except Individu.DoesNotExist:
                    try:
                        organisasi = Organisasi.objects.get(id_adopter=adopter)
                        adopter_info = {
                            'type': 'organisasi',
                            'nama_organisasi': organisasi.nama_organisasi,
                            'npp': organisasi.npp
                        }
                    except Organisasi.DoesNotExist:
                        adopter_info = {
                            'type': 'unknown'
                        }
                
                return JsonResponse({
                    'exists': True,
                    'is_adopter': True,
                    'pengunjung': {
                        'username': pengguna.username,
                        'email': pengguna.email,
                        'nama': f"{pengguna.nama_depan} {pengguna.nama_belakang}",
                        'alamat': pengunjung.alamat
                    },
                    'adopter': adopter_info
                })
                
            except Adopter.DoesNotExist:
                # Pengunjung exists but is not an adopter yet
                return JsonResponse({
                    'exists': True,
                    'is_adopter': False,
                    'pengunjung': {
                        'username': pengguna.username,
                        'email': pengguna.email,
                        'nama': f"{pengguna.nama_depan} {pengguna.nama_belakang}",
                        'alamat': pengunjung.alamat
                    }
                })
                
        except Pengunjung.DoesNotExist:
            # User exists but doesn't have a pengunjung account
            return JsonResponse({
                'exists': True,
                'is_pengunjung': False,
                'pengguna': {
                    'username': pengguna.username,
                    'email': pengguna.email,
                    'nama': f"{pengguna.nama_depan} {pengguna.nama_belakang}"
                }
            })
            
    except Pengguna.DoesNotExist:
        # Username doesn't exist
        return JsonResponse({
            'exists': False
        })