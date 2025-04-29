from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta, datetime
import uuid

from .models import (
    Adopsi, Adopter, Individu, Organisasi
)
from rekam_medis.models import CatatanMedis
from accounts.models import (Pengunjung, Pengguna, StafAdmin)
from satwa.models import Hewan
from .forms import AdopsiForm, PerpanjangAdopsiForm

# @login_required
def detail_hewan(request, hewan_id):
    """Menampilkan detail hewan untuk admin"""
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except StafAdmin.DoesNotExist:
        pass  # Untuk development biarkan akses semua

    hewan = get_object_or_404(Hewan, id=hewan_id)
    
    # Ambil status adopsi hewan
    current_adoption = Adopsi.objects.filter(
    id_hewan=hewan,
    tgl_berhenti_adopsi__gt=timezone.now().date()
        ).values(
            'id_adopter', 
            'id_hewan',
            'status_pembayaran',
            'tgl_mulai_adopsi',
            'tgl_berhenti_adopsi',
            'kontribusi_finansial'
        ).order_by('-tgl_mulai_adopsi')
    
    current_adoption = current_adoption.first()

    if not current_adoption:
        messages.error(request, "Hewan ini belum diadopsi.")
        return redirect('adopsi:admin_dashboard')

    class AdoptionObject:
        pass

    adoption = AdoptionObject()
    adoption.id_hewan = hewan
    adoption.status_adopsi = current_adoption['status_pembayaran']  
    adoption.tgl_mulai_adopsi = current_adoption['tgl_mulai_adopsi'] 
    adoption.tgl_berhenti_adopsi = current_adoption['tgl_berhenti_adopsi'] 

    # Cek tipe adopter
    adopter = get_object_or_404(Adopter, id_adopter=current_adoption['id_adopter'])

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

    context = {
        'adoption': adoption,
        'hewan': hewan,
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': adoption.tgl_mulai_adopsi.strftime('%Y-%m-%d'),
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


def dashboard_adopter(request):
    try:
        pengunjung = Pengunjung.objects.get(username_p__username=request.session['username'])
        adopter = Adopter.objects.get(username_adopter=pengunjung)
    except (Pengunjung.DoesNotExist, Adopter.DoesNotExist):
        messages.error(request, "Anda belum terdaftar sebagai adopter.")
        return redirect('adopsi:list_hewan')

    adoptions_query = Adopsi.objects.filter(id_adopter=adopter).values(
        'id_adopter__id_adopter',
        'id_hewan__id',
        'id_hewan__nama',
        'id_hewan__spesies',
        'id_hewan__url_foto',
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    ).order_by('-tgl_mulai_adopsi')

    adoptions = []
    for adoption in adoptions_query:
        adoptions.append({
            'id_adopter__id_adopter': adoption['id_adopter__id_adopter'],
            'id_hewan__id': adoption['id_hewan__id'],
            'id_hewan__nama': adoption['id_hewan__nama'],
            'id_hewan__spesies': adoption['id_hewan__spesies'],
            'id_hewan__url_foto': adoption['id_hewan__url_foto'],
            'tgl_mulai_adopsi': adoption['tgl_mulai_adopsi'],
            'tgl_mulai_adopsi_str': adoption['tgl_mulai_adopsi'].strftime('%Y-%m-%d'),
            'tgl_berhenti_adopsi': adoption['tgl_berhenti_adopsi'],
            'kontribusi_finansial': adoption['kontribusi_finansial'],
            'status_pembayaran': adoption['status_pembayaran'],
        })

    context = {
        'adopter': adopter,
        'adoptions': adoptions,
        'now': timezone.now(),
    }
    return render(request, 'adopsi/dashboard_adopter.html', context)

# @login_required
def detail_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Menampilkan detail adopsi untuk adopter (user)"""
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')

    adopter = get_object_or_404(Adopter, id_adopter=id_adopter)
    hewan = get_object_or_404(Hewan, id=id_hewan)

    queryset = Adopsi.objects.filter(
        id_adopter=adopter,
        id_hewan=hewan,
        tgl_mulai_adopsi=tgl_mulai
    ).values(
        'id_adopter__id_adopter',
        'id_hewan__id',
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    )

    adopsi_list = list(queryset)

    if not adopsi_list:
        messages.error(request, "Adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')

    adopsi_data = adopsi_list[0]

    # Create dummy AdopsiObject
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.id_adopter = adopter
    adopsi.id_hewan = hewan
    adopsi.status_pembayaran = adopsi_data['status_pembayaran']
    adopsi.tgl_mulai_adopsi = adopsi_data['tgl_mulai_adopsi']
    adopsi.tgl_berhenti_adopsi = adopsi_data['tgl_berhenti_adopsi']
    adopsi.kontribusi_finansial = adopsi_data['kontribusi_finansial']

    # Cek tipe adopter
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

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung': adopter.username_adopter,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': adopsi.tgl_mulai_adopsi.strftime('%Y-%m-%d'),
    }

    return render(request, 'adopsi/detail_adopsi.html', context)

def perpanjang_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    adopter = get_object_or_404(Adopter, id_adopter=id_adopter)
    hewan = get_object_or_404(Hewan, id=id_hewan)  # 🛠 ini fix-nya
    tgl_mulai = timezone.datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()

    adopsi_query = Adopsi.objects.filter(
    id_adopter=adopter,
    id_hewan=hewan,
    tgl_mulai_adopsi=tgl_mulai
    ).values(
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    ).order_by('tgl_mulai_adopsi')

    adopsi_data = adopsi_query.first()


    if not adopsi_data:
            messages.error(request, "Data adopsi tidak ditemukan.")
            return redirect('adopsi:dashboard_adopter')

        # Dummy adopsi
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.status_pembayaran = adopsi_data['status_pembayaran']
    adopsi.tgl_mulai_adopsi = adopsi_data['tgl_mulai_adopsi']
    adopsi.tgl_berhenti_adopsi = adopsi_data['tgl_berhenti_adopsi']
    adopsi.kontribusi_finansial = adopsi_data['kontribusi_finansial']


    if request.method == 'POST':
        periode_bulan = int(request.POST.get('periode'))
        kontribusi = int(request.POST.get('kontribusi'))

        # Update adopsi
        adopsi.tgl_berhenti_adopsi += timezone.timedelta(days=30 * periode_bulan)
        adopsi.kontribusi_finansial += kontribusi
        adopsi.status_pembayaran = 'tertunda'
        adopsi.save()

        # Update total kontribusi adopter
        adopter.total_kontribusi += kontribusi
        adopter.save()

        messages.success(request, f"Adopsi {hewan.nama} berhasil diperpanjang.")
        return redirect('adopsi:dashboard_adopter')

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
    }
    return render(request, 'adopsi/perpanjang_form.html', context)

# @login_required
# views.py

# @login_required
def berhenti_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Berhenti adopsi"""
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')

    adopsi_query = Adopsi.objects.filter(
        id_adopter__id_adopter=id_adopter,
        id_hewan__id=id_hewan,
        tgl_mulai_adopsi=tgl_mulai
    ).values(
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    )

    adopsi_data = adopsi_query.first()

    if not adopsi_data:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')

    # Dummy adopsi buat template
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.status_pembayaran = adopsi_data['status_pembayaran']
    adopsi.tgl_mulai_adopsi = adopsi_data['tgl_mulai_adopsi']
    adopsi.tgl_berhenti_adopsi = adopsi_data['tgl_berhenti_adopsi']
    adopsi.kontribusi_finansial = adopsi_data['kontribusi_finansial']

    adopsi_real = Adopsi.objects.get(
        id_adopter__id_adopter=id_adopter,
        id_hewan__id=id_hewan,
        tgl_mulai_adopsi=tgl_mulai
    )

    if request.method == 'POST':
        adopsi_real.tgl_berhenti_adopsi = timezone.now().date()
        adopsi_real.save()
        
        is_admin = StafAdmin.objects.filter(username_sa=request.user.username).exists()
        messages.success(request, "Adopsi berhasil dihentikan.")

        if is_admin:
            return redirect('adopsi:admin_daftar_adopsi')
        else:
            return redirect('adopsi:dashboard_adopter')

    hewan = get_object_or_404(Hewan, id=id_hewan)

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
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
    pending_payments = Adopsi.objects.filter(status_pembayaran='Tertunda').count()
    
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
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except:
        pass

    adopter = get_object_or_404(Adopter, id_adopter=adopter_id)

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

    adoptions_query = Adopsi.objects.filter(id_adopter=adopter).values(
        'id_adopter__id_adopter',
        'id_hewan__id',
        'id_hewan__nama',
        'id_hewan__spesies',
        'id_hewan__url_foto',
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    ).order_by('-tgl_mulai_adopsi')

    adoptions = []
    for adoption in adoptions_query:
        adoptions.append({
            'id_adopter__id_adopter': adoption['id_adopter__id_adopter'],
            'id_hewan__id': adoption['id_hewan__id'],
            'id_hewan__nama': adoption['id_hewan__nama'],
            'id_hewan__spesies': adoption['id_hewan__spesies'],
            'id_hewan__url_foto': adoption['id_hewan__url_foto'],
            'tgl_mulai_adopsi': adoption['tgl_mulai_adopsi'],
            'tgl_mulai_adopsi_str': adoption['tgl_mulai_adopsi'].strftime('%Y-%m-%d'),  # 🛠 Tambahin ini
            'tgl_berhenti_adopsi': adoption['tgl_berhenti_adopsi'],
            'kontribusi_finansial': adoption['kontribusi_finansial'],
            'status_pembayaran': adoption['status_pembayaran'],
        })


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
# @login_required
def admin_update_payment(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Update status pembayaran adopsi oleh admin"""
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except StafAdmin.DoesNotExist:
        pass  # allow development

    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:admin_dashboard')

    adopsi_query = Adopsi.objects.filter(
        id_adopter__id_adopter=id_adopter,
        id_hewan__id=id_hewan,
        tgl_mulai_adopsi=tgl_mulai
    ).values(
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    )

    adopsi_data = adopsi_query.first()

    if not adopsi_data:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')

    # Bikin dummy object
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.status_pembayaran = adopsi_data['status_pembayaran']
    adopsi.tgl_mulai_adopsi = adopsi_data['tgl_mulai_adopsi']
    adopsi.tgl_berhenti_adopsi = adopsi_data['tgl_berhenti_adopsi']
    adopsi.kontribusi_finansial = adopsi_data['kontribusi_finansial']

    # Dapetin objek asli untuk save
    adopsi_real = Adopsi.objects.get(
        id_adopter__id_adopter=id_adopter,
        id_hewan__id=id_hewan,
        tgl_mulai_adopsi=tgl_mulai
    )

    if request.method == 'POST':
        new_status = request.POST.get('status_pembayaran')
        if new_status in ['tertunda', 'lunas']:
            adopsi_real.status_pembayaran = new_status
            adopsi_real.save()
            messages.success(request, f"Status pembayaran adopsi diperbarui menjadi '{new_status}'.")
        else:
            messages.error(request, "Status pembayaran tidak valid.")
        
        return redirect('adopsi:admin_detail_adopsi', id_adopter=id_adopter, id_hewan=id_hewan, tgl_mulai_adopsi=tgl_mulai_adopsi)

    hewan = get_object_or_404(Hewan, id=id_hewan)

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
    }
    return render(request, 'adopsi/admin/update_payment.html', context)

    
# @login_required
def admin_detail_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Menampilkan detail adopsi untuk admin"""
    try:
        staf_admin = StafAdmin.objects.get(username_sa=request.user.username)
    except StafAdmin.DoesNotExist:
        pass  # Untuk development biarkan akses semua

    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:admin_dashboard')

    adopter = get_object_or_404(Adopter, id_adopter=id_adopter)
    hewan = get_object_or_404(Hewan, id=id_hewan)

    queryset = Adopsi.objects.filter(
        id_adopter=adopter,
        id_hewan=hewan,
        tgl_mulai_adopsi=tgl_mulai
    ).values(
        'id_adopter__id_adopter',
        'id_hewan__id',
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    )

    adopsi_list = list(queryset)

    if not adopsi_list:
        messages.error(request, "Adopsi tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')

    adopsi_data = adopsi_list[0]

    # Create dummy adopsi object for template
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.id_adopter = adopter
    adopsi.id_hewan = hewan
    adopsi.status_pembayaran = adopsi_data['status_pembayaran']
    adopsi.tgl_mulai_adopsi = adopsi_data['tgl_mulai_adopsi']
    adopsi.tgl_berhenti_adopsi = adopsi_data['tgl_berhenti_adopsi']
    adopsi.kontribusi_finansial = adopsi_data['kontribusi_finansial']

    # Cek tipe adopter
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

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung': adopter.username_adopter,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': adopsi.tgl_mulai_adopsi.strftime('%Y-%m-%d'),
    }

    return render(request, 'adopsi/admin/detail_adopsi.html', context)


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
        return redirect('adopsi:admin_detail_adopsi', id_adopter=adopsi.id_adopter.id_adopter, id_hewan=adopsi.id_hewan.id, tgl_mulai_adopsi=adopsi.tgl_mulai_adopsi.strftime('%Y-%m-%d'))
    
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

from rekam_medis.models import CatatanMedis

def laporan_kondisi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Menampilkan laporan kondisi hewan untuk adopter"""
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')

    adopter = get_object_or_404(Adopter, id_adopter=id_adopter)
    hewan = get_object_or_404(Hewan, id=id_hewan)

    adopsi_query = Adopsi.objects.filter(
    id_adopter=adopter,
    id_hewan=hewan,
    tgl_mulai_adopsi=tgl_mulai
        ).values(
            'status_pembayaran',
            'tgl_mulai_adopsi',
            'tgl_berhenti_adopsi',
            'kontribusi_finansial'
        ).order_by('tgl_mulai_adopsi')

    adopsi_data = adopsi_query.first()

    if not adopsi_data:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')

    # Bikin dummy object
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.status_pembayaran = adopsi_data['status_pembayaran']
    adopsi.tgl_mulai_adopsi = adopsi_data['tgl_mulai_adopsi']
    adopsi.tgl_berhenti_adopsi = adopsi_data['tgl_berhenti_adopsi']
    adopsi.kontribusi_finansial = adopsi_data['kontribusi_finansial']

    # Medical records
    medical_records_query = CatatanMedis.objects.filter(
    id_hewan=hewan,
    tanggal_pemeriksaan__gte=tgl_mulai
        ).values(
            'id_hewan',
            'tanggal_pemeriksaan',
            'diagnosis',
            'pengobatan',
            'status_kesehatan',
            'catatan_tindak_lanjut'
        ).order_by('-tanggal_pemeriksaan')

    medical_records = list(medical_records_query)


    context = {
        'adopsi': adopsi,
        'hewan': hewan,
        'adopter': adopter,
        'medical_records': medical_records,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': tgl_mulai.strftime('%Y-%m-%d'),
    }
    return render(request, 'adopsi/laporan_kondisi.html', context)

def sertifikat_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Menampilkan sertifikat adopsi"""
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')

    adopter = get_object_or_404(Adopter, id_adopter=id_adopter)
    hewan = get_object_or_404(Hewan, id=id_hewan)

    adopsi_query = Adopsi.objects.filter(
        id_adopter=adopter,
        id_hewan=hewan,
        tgl_mulai_adopsi=tgl_mulai
    ).values(
        'id_adopter__id_adopter',
        'id_hewan__id',
        'status_pembayaran',
        'tgl_mulai_adopsi',
        'tgl_berhenti_adopsi',
        'kontribusi_finansial'
    ).order_by('tgl_mulai_adopsi')

    adopsi_query = adopsi_query.first()

    if not adopsi_query:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')

    # Buat manual dict (kayak yang admin_detail_adopter)
    adopsi = {
        'id_adopter__id_adopter': adopsi_query['id_adopter__id_adopter'],
        'id_hewan__id': adopsi_query['id_hewan__id'],
        'status_pembayaran': adopsi_query['status_pembayaran'],
        'tgl_mulai_adopsi': adopsi_query['tgl_mulai_adopsi'],
        'tgl_mulai_adopsi_str': adopsi_query['tgl_mulai_adopsi'].strftime('%Y-%m-%d'),
        'tgl_berhenti_adopsi': adopsi_query['tgl_berhenti_adopsi'],
        'tgl_berhenti_adopsi_str': adopsi_query['tgl_berhenti_adopsi'].strftime('%Y-%m-%d'),
        'kontribusi_finansial': adopsi_query['kontribusi_finansial'],
    }

    # Cek tipe adopter
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

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung_username': adopter.username_adopter.username_p.username,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': adopsi['tgl_mulai_adopsi_str'],
        'tgl_berhenti_adopsi_str': adopsi['tgl_berhenti_adopsi_str'],
    }

    return render(request, 'adopsi/sertifikat_adopsi.html', context)

def admin_hapus_adopter(request, adopter_id):
    adopter = get_object_or_404(Adopter, id_adopter=adopter_id)
    adopter.delete()
    messages.success(request, "Data adopter berhasil dihapus.")
    return redirect('adopsi:admin_dashboard')

