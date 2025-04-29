from django.shortcuts import render, redirect

from adopsi.models import Adopter
from .forms import RegisterForm, LoginForm
from .models import Pengguna, Pengunjung, DokterHewan, PenjagaHewan, PelatihHewan, StafAdmin
import uuid
from django.contrib import messages

def register_pengunjung_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        nama_depan = request.POST['nama_depan']
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST['nama_belakang']
        no_telepon = request.POST['no_telepon']
        alamat = request.POST['alamat']
        tgl_lahir = request.POST['tgl_lahir']

        # Simpan ke Pengguna
        pengguna = Pengguna.objects.create(
            username=username,
            email=email,
            password=password,
            nama_depan=nama_depan,
            nama_tengah=nama_tengah,
            nama_belakang=nama_belakang,
            no_telepon=no_telepon
        )

        # Simpan ke Pengunjung
        Pengunjung.objects.create(
            username_p=pengguna,
            alamat=alamat,
            tgl_lahir=tgl_lahir
        )

        return redirect('login')

    return render(request, 'accounts/register_pengunjung.html')

def register_staff_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        nama_depan = request.POST['nama_depan']
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST['nama_belakang']
        no_telepon = request.POST['no_telepon']
        role_staff = request.POST['role_staff']

        # Simpan ke Pengguna
        pengguna = Pengguna.objects.create(
            username=username,
            email=email,
            password=password,
            nama_depan=nama_depan,
            nama_tengah=nama_tengah,
            nama_belakang=nama_belakang,
            no_telepon=no_telepon
        )

        # Generate UUID untuk ID staf
        import uuid
        id_staf = uuid.uuid4()

        # Simpan ke tabel sesuai pilihan role staff
        if role_staff == 'Penjaga Hewan':
            PenjagaHewan.objects.create(username_jh=pengguna, id_staf=id_staf)
        elif role_staff == 'Pelatih Hewan':
            PelatihHewan.objects.create(username_lh=pengguna, id_staf=id_staf)
        elif role_staff == 'Staf Administrasi':
            StafAdmin.objects.create(username_sa=pengguna, id_staf=id_staf)

        return redirect('login')

    return render(request, 'accounts/register_staff.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                user = Pengguna.objects.get(email=email, password=password)
                request.session['email'] = user.email
                request.session['nama_lengkap'] = f"{user.nama_depan} {user.nama_belakang}"
                request.session['username'] = user.username

                messages.success(request, f"Selamat datang, {user.nama_depan}!")
                return redirect('dashboard')  # <- langsung ke dashboard
            except Pengguna.DoesNotExist:
                messages.error(request, "Email atau password salah.")
        else:
            messages.error(request, "Form tidak valid.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def register_dokter_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        nama_depan = request.POST['nama_depan']
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST['nama_belakang']
        no_telepon = request.POST['no_telepon']
        no_str = request.POST['no_str']

        # Simpan ke Pengguna
        pengguna = Pengguna.objects.create(
            username=username,
            email=email,
            password=password,
            nama_depan=nama_depan,
            nama_tengah=nama_tengah,
            nama_belakang=nama_belakang,
            no_telepon=no_telepon
        )

        # Simpan ke Dokter Hewan
        DokterHewan.objects.create(
            username_dh=pengguna,
            no_str=no_str
        )

        return redirect('login')

    return render(request, 'accounts/register_dokter.html')

def logout_view(request):
    request.session.flush()  # Clear semua session
    messages.success(request, "Berhasil logout.")
    return redirect('login')

def choose_role_view(request):
    return render(request, 'accounts/choose_role.html')

def navbar_view(request):
    user_role = "guest"
    username = request.session.get('username')
    
    if username:
        # Check role by querying directly with username
        if DokterHewan.objects.filter(username_dh=username).exists():
            role = "Dokter Hewan"
            print("Dokter Hewan")
        elif PenjagaHewan.objects.filter(username_jh=username).exists():
            role = "Penjaga Hewan"
            print("Penjaga Hewan")
        elif StafAdmin.objects.filter(username_sa=username).exists():
            role = "Staf Administrasi"
            print("Staf Administrasi")
        elif PelatihHewan.objects.filter(username_lh=username).exists():
            role = "Staf Pelatih Pertunjukan"
            print("Staf Pelatih Pertunjukan")
        elif Adopter.objects.filter(username_adopter=username).exists():
            if Pengunjung.objects.filter(username_p=username).exists():
                role = "pengunjung_adopter"
            else:
                role = "adopter"
        elif Pengunjung.objects.filter(username_p=username).exists():
            role = "Pengunjung"
            print("Pengunjung")
            
    return render(request, 'accounts/navbar.html', {'user_role': role})