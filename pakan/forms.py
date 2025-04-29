from django import forms
from .models import Pakan

class PakanForm(forms.ModelForm):
    class Meta:
        model = Pakan
        fields = ['jenis', 'jumlah', 'jadwal']
        widgets = {
            'jadwal': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class EditPakanForm(forms.ModelForm):
    class Meta:
        model = Pakan
        fields = ['jenis', 'jumlah', 'jadwal']
        widgets = {
            'jadwal': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }