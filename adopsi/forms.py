
from django import forms
from django.utils import timezone
from .models import Adopsi, Individu, Organisasi, Adopter

class AdopsiForm(forms.ModelForm):
    PERIODE_CHOICES = [
        (3, '3 bulan'),
        (6, '6 bulan'),
        (12, '12 bulan'),
    ]
    
    periode = forms.ChoiceField(choices=PERIODE_CHOICES, widget=forms.Select)
    
    class Meta:
        model = Adopsi
        fields = ['kontribusi_finansial']
        widgets = {
            'kontribusi_finansial': forms.NumberInput(attrs={'min': '100000'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.hewan = kwargs.pop('hewan', None)
        self.adopter = kwargs.pop('adopter', None)
        super(AdopsiForm, self).__init__(*args, **kwargs)
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.id_hewan = self.hewan
        instance.id_adopter = self.adopter
        
        # Menentukan tanggal mulai dan selesai berdasarkan periode
        instance.tgl_mulai_adopsi = timezone.now().date()
        periode_bulan = int(self.cleaned_data['periode'])
        instance.tgl_berhenti_adopsi = instance.tgl_mulai_adopsi + timezone.timedelta(days=30*periode_bulan)
        
        if commit:
            instance.save()
        return instance

class IndividuForm(forms.ModelForm):
    class Meta:
        model = Individu
        fields = ['nik', 'nama']
        widgets = {
            'nik': forms.TextInput(attrs={'placeholder': 'Masukkan 16 digit NIK', 'maxlength': '16'}),
            'nama': forms.TextInput(attrs={'placeholder': 'Nama lengkap'})
        }

class OrganisasiForm(forms.ModelForm):
    class Meta:
        model = Organisasi
        fields = ['npp', 'nama_organisasi']
        widgets = {
            'npp': forms.TextInput(attrs={'placeholder': 'Masukkan 8 digit NPP', 'maxlength': '8'}),
            'nama_organisasi': forms.TextInput(attrs={'placeholder': 'Nama organisasi/perusahaan'})
        }
