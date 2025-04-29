from django.shortcuts import render, get_object_or_404, redirect
import uuid
from rekam_medis.models import CatatanMedis
from .forms import TambahRekamMedisForm, RekamMedisEditForm
from django.contrib.auth.decorators import login_required
from django import forms

# def list_rekam_medis(request):
#     rekam_medis = CatatanMedis.objects.all().order_by('tanggal_pemeriksaan') 
#     return render(request, 'rekam_medis/rekam_medis_list.html', {'rekam_medis': rekam_medis})

# pake dummy dulu 
def list_rekam_medis(request):
    rekam_medis = [
        {
            'id_hewan': uuid.UUID('550e8400-e29b-41d4-a716-446655440000'),
            'tanggal_pemeriksaan': '2025-04-22',
            'nama_dokter': 'Brandon Charles Clark',
            'status_kesehatan': 'Sakit',
            'diagnosis': 'infeksi ringan',
            'pengobatan': 'antibiotik 5 hari',
            'catatan_tindak_lanjut': 'perlu observasi ulang',
        },
        {
            'id_hewan': uuid.UUID('550e8400-e29b-41d4-a716-446655440001'),
            'tanggal_pemeriksaan': '2025-04-19',
            'nama_dokter': 'Shawn Jason Walton',
            'status_kesehatan': 'Sehat',
            'diagnosis': '-',
            'pengobatan': '-',
            'catatan_tindak_lanjut': '-',
        },
        {
            'id_hewan': uuid.UUID('550e8400-e29b-41d4-a716-446655440002'),
            'tanggal_pemeriksaan': '2025-04-15',
            'nama_dokter': 'Tanya Robinson',
            'status_kesehatan': 'Sakit',
            'diagnosis': 'demam',
            'pengobatan': 'obat penurun panas',
            'catatan_tindak_lanjut': 'kontrol ulang 3 hari',
        },
        {
            'id_hewan': uuid.UUID('550e8400-e29b-41d4-a716-446655440003'),
            'tanggal_pemeriksaan': '2025-04-10',
            'nama_dokter': 'Andrea Rachel Davis',
            'status_kesehatan': 'Sehat',
            'diagnosis': '-',
            'pengobatan': '-',
            'catatan_tindak_lanjut': '-',
        },
        {
            'id_hewan': uuid.UUID('550e8400-e29b-41d4-a716-446655440004'),
            'tanggal_pemeriksaan': '2025-04-05',
            'nama_dokter': 'Michael Kaufman',
            'status_kesehatan': 'Sehat',
            'diagnosis': '-',
            'pengobatan': '-',
            'catatan_tindak_lanjut': '-',
        },
    ]
    rekam_medis.sort(key=lambda x: x['tanggal_pemeriksaan'])
    return render(request, 'rekam_medis/rekam_medis_list.html', {'rekam_medis': rekam_medis})

# @login_required
def tambah_rekam_medis(request):
    if request.method == 'POST':
        form = TambahRekamMedisForm(request.POST)
        if form.is_valid():
            rekam_medis = form.save(commit=False)
            rekam_medis.username_dh = request.user.dokterhewan 
            rekam_medis.save()
            return redirect('rekam_medis:list_rekam_medis')
    else:
        form = TambahRekamMedisForm()

    return render(request, 'rekam_medis/rekam_medis_form.html', {'form': form})

# @login_required
# def edit_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
#     rekam_medis = CatatanMedis.objects.get(id_hewan=id_hewan, tanggal_pemeriksaan=tanggal_pemeriksaan)
#     if request.method == 'POST':
#         form = RekamMedisEditForm(request.POST, instance=rekam_medis)
#         if form.is_valid():
#             form.save()
#             return redirect('rekam_medis:list_rekam_medis')
#     else:
#         form = RekamMedisEditForm(instance=rekam_medis)
#     return render(request, 'rekam_medis/rekam_medis_edit.html', {'form': form})

# Dummy form untuk edit
class DummyEditForm(forms.Form):
    diagnosis = forms.CharField(initial="Dummy Diagnosis", required=False)
    pengobatan = forms.CharField(initial="Dummy Pengobatan", required=False)
    catatan_tindak_lanjut = forms.CharField(initial="Dummy Catatan", required=False)

def edit_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
    if request.method == 'POST':
        form = DummyEditForm(request.POST)
        if form.is_valid():
            return redirect('rekam_medis:list_rekam_medis')
    else:
        form = DummyEditForm()

    return render(request, 'rekam_medis/rekam_medis_edit.html', {'form': form})

# @login_required
# def hapus_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
#     rekam_medis = get_object_or_404(CatatanMedis, id_hewan=id_hewan, tanggal_pemeriksaan=tanggal_pemeriksaan)
#     if request.method == 'POST':
#         rekam_medis.delete()
#         return redirect('rekam_medis:list_rekam_medis')
#     return render(request, 'rekam_medis/rekam_medis_confirm_delete.html', {'rekam_medis': rekam_medis})

# delete dummy  ya
def hapus_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
    if request.method == 'POST':
        return redirect('rekam_medis:list_rekam_medis')
    
    # INI buat nampilin halaman konfirmasi
    return render(request, 'rekam_medis/rekam_medis_confirm_delete.html', {
        'id_hewan': id_hewan,
        'tanggal_pemeriksaan': tanggal_pemeriksaan
    })