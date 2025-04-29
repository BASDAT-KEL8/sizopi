from django import forms
from rekam_medis.models import CatatanMedis

class TambahRekamMedisForm(forms.ModelForm):
    nama_dokter = forms.CharField(
        label='Nama Dokter',
        required=True,
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 w-full', 'placeholder': 'Nama dokter pemeriksa'})
    )

    class Meta:
        model = CatatanMedis
        fields = ['tanggal_pemeriksaan', 'status_kesehatan', 'diagnosis', 'pengobatan']
        widgets = {
            'tanggal_pemeriksaan': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded p-2 w-full'}),
            'status_kesehatan': forms.Select(choices=[('Sehat', 'Sehat'), ('Sakit', 'Sakit')], attrs={'class': 'border rounded p-2 w-full'}),
            'diagnosis': forms.TextInput(attrs={'class': 'border rounded p-2 w-full', 'placeholder': 'Opsional'}),
            'pengobatan': forms.TextInput(attrs={'class': 'border rounded p-2 w-full', 'placeholder': 'Opsional'}),
        }

    def __init__(self, *args, **kwargs):
        dokter = kwargs.pop('dokter', None)
        super().__init__(*args, **kwargs)
        if dokter:
            self.fields['nama_dokter'].initial = f"{dokter.nama_depan} {dokter.nama_belakang}"

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Nama dokter tidak disimpan ke database karena tidak ada di model
        if commit:
            instance.save()
        return instance

class RekamMedisEditForm(forms.ModelForm):
    catatan_tindak_lanjut = forms.CharField(
        label='Catatan Tindak Lanjut', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 w-full', 'placeholder': 'Opsional'})
    )
    diagnosis = forms.CharField(
        label='Diagnosa Baru',
        required=False,
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 w-full', 'placeholder': 'Opsional'})
    )
    pengobatan = forms.CharField(
        label='Pengobatan Baru',
        required=False,
        widget=forms.TextInput(attrs={'class': 'border rounded p-2 w-full', 'placeholder': 'Opsional'})
    )

    class Meta:
        model = CatatanMedis
        fields = ['catatan_tindak_lanjut', 'diagnosis', 'pengobatan']
