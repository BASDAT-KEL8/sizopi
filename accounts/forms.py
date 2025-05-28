from django import forms

class RegisterForm(forms.Form):
    username = forms.CharField(max_length=50)
    email = forms.EmailField(max_length=100)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Konfirmasi Password', widget=forms.PasswordInput)
    nama_depan = forms.CharField(max_length=50)
    nama_tengah = forms.CharField(max_length=50, required=False)
    nama_belakang = forms.CharField(max_length=50)
    no_telepon = forms.CharField(max_length=15)
    role = forms.ChoiceField(choices=[
        ('pengunjung', 'Pengunjung'),
        ('dokter', 'Dokter Hewan'),
        ('penjaga', 'Penjaga Hewan'),
        ('pelatih', 'Pelatih Hewan'),
        ('admin', 'Staf Admin'),
    ])

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
