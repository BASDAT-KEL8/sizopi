from django.shortcuts import render, get_object_or_404, redirect

from rekam_medis.models import CatatanMedis
from .forms import TambahRekamMedisForm, RekamMedisEditForm
from django.contrib.auth.decorators import login_required

def list_rekam_medis(request):
    rekam_medis = CatatanMedis.objects.all()
    return render(request, 'rekam_medis/rekam_medis_list.html', {'rekam_medis': rekam_medis})

@login_required
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

@login_required
def edit_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
    rekam_medis = CatatanMedis.objects.get(id_hewan=id_hewan, tanggal_pemeriksaan=tanggal_pemeriksaan)
    if request.method == 'POST':
        form = RekamMedisEditForm(request.POST, instance=rekam_medis)
        if form.is_valid():
            form.save()
            return redirect('rekam_medis:list_rekam_medis')
    else:
        form = RekamMedisEditForm(instance=rekam_medis)
    return render(request, 'rekam_medis/rekam_medis_edit.html', {'form': form})

@login_required
def hapus_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
    rekam_medis = get_object_or_404(CatatanMedis, id_hewan=id_hewan, tanggal_pemeriksaan=tanggal_pemeriksaan)
    if request.method == 'POST':
        rekam_medis.delete()
        return redirect('rekam_medis:list_rekam_medis')
    return render(request, 'rekam_medis/rekam_medis_confirm_delete.html', {'rekam_medis': rekam_medis})


