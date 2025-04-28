# forms.py
from django import forms
from .models import Adopter
from satwa.models import Hewan

class AdopsiForm(forms.Form):
    """Form untuk pendaftaran adopsi hewan baru"""
    ADOPTER_TYPE_CHOICES = [
        ('individu', 'Individu'),
        ('organisasi', 'Organisasi'),
    ]
    
    PERIODE_CHOICES = [
        (3, '3 Bulan'),
        (6, '6 Bulan'),
        (12, '12 Bulan'),
    ]
    
    adopter_type = forms.ChoiceField(
        label='Tipe Adopter',
        choices=ADOPTER_TYPE_CHOICES,
        widget=forms.RadioSelect(),
        initial='individu'
    )
    
    # Fields untuk individu
    nama = forms.CharField(
        label='Nama Lengkap',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    nik = forms.CharField(
        label='NIK',
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Fields untuk organisasi
    npp = forms.CharField(
        label='NPP (Nomor Pokok Perusahaan)',
        max_length=8,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Fields umum
    alamat = forms.CharField(
        label='Alamat',
        max_length=200,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    no_telepon = forms.CharField(
        label='Nomor Telepon',
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    kontribusi = forms.IntegerField(
        label='Nominal Kontribusi Finansial (Rp)',
        min_value=500000,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    periode = forms.ChoiceField(
        label='Periode Adopsi',
        choices=PERIODE_CHOICES,
        initial=3,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        adopter_type = cleaned_data.get('adopter_type')
        
        if adopter_type == 'individu':
            # Validasi field individu
            nama = cleaned_data.get('nama')
            nik = cleaned_data.get('nik')
            
            if not nama:
                self.add_error('nama', 'Nama lengkap wajib diisi untuk individu')
            
            if not nik:
                self.add_error('nik', 'NIK wajib diisi untuk individu')
            elif len(nik) != 16:
                self.add_error('nik', 'NIK harus terdiri dari 16 digit')
        
        elif adopter_type == 'organisasi':
            # Validasi field organisasi
            nama = cleaned_data.get('nama')
            npp = cleaned_data.get('npp')
            
            if not nama:
                self.add_error('nama', 'Nama organisasi wajib diisi')
            
            if not npp:
                self.add_error('npp', 'NPP wajib diisi untuk organisasi')
            elif len(npp) != 8:
                self.add_error('npp', 'NPP harus terdiri dari 8 karakter')
        
        return cleaned_data


class PerpanjangAdopsiForm(forms.Form):
    """Form untuk perpanjangan periode adopsi hewan"""
    PERIODE_CHOICES = [
        (3, '3 Bulan'),
        (6, '6 Bulan'),
        (12, '12 Bulan'),
    ]
    
    kontribusi = forms.IntegerField(
        label='Nominal Kontribusi Finansial (Rp)',
        min_value=500000,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    periode = forms.ChoiceField(
        label='Perpanjang Periode Adopsi',
        choices=PERIODE_CHOICES,
        initial=3,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        kontribusi = cleaned_data.get('kontribusi')
        
        if kontribusi < 500000:
            self.add_error('kontribusi', 'Minimal kontribusi adalah Rp 500.000')
        
        return cleaned_data