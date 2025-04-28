from django import forms
from accounts.models import Pengguna

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Konfirmasi Password', widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[
        ('pengunjung', 'Pengunjung'),
        ('dokter', 'Dokter Hewan'),
        ('penjaga', 'Penjaga Hewan'),
        ('pelatih', 'Pelatih Hewan'),
        ('admin', 'Staf Admin'),
    ])

    class Meta:
        model = Pengguna
        fields = ['username', 'email', 'nama_depan', 'nama_tengah', 'nama_belakang', 'no_telepon']

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 != password2:
            raise forms.ValidationError("Password dan konfirmasi tidak sama!")
        return cleaned_data
    
class LoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)


    