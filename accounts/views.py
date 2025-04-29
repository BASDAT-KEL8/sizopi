from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from .models import Pengguna, Pengunjung, DokterHewan, PenjagaHewan, PelatihHewan, StafAdmin
from adopsi.models import Adopter
import uuid

def choose_role_view(request):
    return render(request, 'accounts/choose_role.html')

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

def dashboard_view(request):
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    context = {
        'nama_lengkap': request.session.get('nama_lengkap', ''),
        'username': request.session.get('username', '')
    }
    
    return render(request, 'accounts/dashboard.html', context)

def profile_view(request):
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.session['username']
    
    try:
        user = Pengguna.objects.get(username=username)
        
        # Determine user role and get additional data
        user_data = {'pengguna': user}
        
        # Check for pengunjung
        try:
            pengunjung = Pengunjung.objects.get(username_p=user)
            user_data['role'] = 'pengunjung'
            user_data['pengunjung'] = pengunjung
        except Pengunjung.DoesNotExist:
            pass
        
        # Check for dokter hewan
        try:
            dokter = DokterHewan.objects.get(username_dh=user)
            user_data['role'] = 'dokter'
            user_data['dokter'] = dokter
        except DokterHewan.DoesNotExist:
            pass
        
        # Check for penjaga hewan
        try:
            penjaga = PenjagaHewan.objects.get(username_jh=user)
            user_data['role'] = 'penjaga'
            user_data['penjaga'] = penjaga
        except PenjagaHewan.DoesNotExist:
            pass
        
        # Check for pelatih hewan
        try:
            pelatih = PelatihHewan.objects.get(username_lh=user)
            user_data['role'] = 'pelatih'
            user_data['pelatih'] = pelatih
        except PelatihHewan.DoesNotExist:
            pass
        
        # Check for staf admin
        try:
            admin = StafAdmin.objects.get(username_sa=user)
            user_data['role'] = 'admin'
            user_data['admin'] = admin
        except StafAdmin.DoesNotExist:
            pass
        
        return render(request, 'accounts/profile.html', user_data)
    
    except Pengguna.DoesNotExist:
        messages.error(request, "User tidak ditemukan.")
        return redirect('login')

def update_profile(request):
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.session['username']
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        try:
            user = Pengguna.objects.get(username=username)
            
            # Handle profile update
            if action == 'update_profile':
                # Update Pengguna data
                user.email = request.POST.get('email', user.email)
                user.nama_depan = request.POST.get('nama_depan', user.nama_depan)
                user.nama_tengah = request.POST.get('nama_tengah', user.nama_tengah)
                user.nama_belakang = request.POST.get('nama_belakang', user.nama_belakang)
                user.no_telepon = request.POST.get('no_telepon', user.no_telepon)
                user.save()
                
                # Update role-specific data
                # For Pengunjung
                try:
                    pengunjung = Pengunjung.objects.get(username_p=user)
                    pengunjung.alamat = request.POST.get('alamat', pengunjung.alamat)
                    if 'tgl_lahir' in request.POST and request.POST['tgl_lahir']:
                        pengunjung.tgl_lahir = request.POST['tgl_lahir']
                    pengunjung.save()
                except Pengunjung.DoesNotExist:
                    pass
                
                # For DokterHewan - we don't update no_str as it's professional ID
                try:
                    dokter = DokterHewan.objects.get(username_dh=user)
                    # Update spesialisasi if that field is added to the model
                    dokter.save()
                except DokterHewan.DoesNotExist:
                    pass
                
                messages.success(request, "Profil berhasil diperbarui.")
            
            # Handle password change
            elif action == 'change_password':
                password_lama = request.POST.get('password_lama')
                password_baru = request.POST.get('password_baru')
                konfirmasi_password = request.POST.get('konfirmasi_password')
                
                # Check if old password is correct
                if user.password != password_lama:
                    messages.error(request, "Password lama tidak sesuai.")
                    return redirect('profile')
                
                # Check if new password and confirmation match
                if password_baru != konfirmasi_password:
                    messages.error(request, "Password baru dan konfirmasi tidak cocok.")
                    return redirect('profile')
                
                # Update password
                user.password = password_baru
                user.save()
                
                messages.success(request, "Password berhasil diubah.")
                
        except Pengguna.DoesNotExist:
            messages.error(request, "User tidak ditemukan.")
        
    return redirect('profile')


def navbar_view(request):
    user_role = "guest"
    role = "guest"
    username = request.session.get('username')
    
    if username:
        try:
            pengguna = Pengguna.objects.get(username=username)

            # Cek role staff
            if DokterHewan.objects.filter(username_dh__username=username).exists():
                role = "Dokter Hewan"
            elif PenjagaHewan.objects.filter(username_jh__username=username).exists():
                role = "Penjaga Hewan"
            elif StafAdmin.objects.filter(username_sa__username=username).exists():
                role = "Staf Administrasi"
            elif PelatihHewan.objects.filter(username_lh__username=username).exists():
                role = "Staf Pelatih Pertunjukan"
            else:
                # Kalau bukan staff, cek apakah dia pengunjung
                try:
                    pengunjung = Pengunjung.objects.get(username_p__username=username)

                    # Cek apakah pengunjung ini juga adopter
                    if Adopter.objects.filter(username_adopter_id=pengunjung.id).exists():
                        role = "pengunjung_adopter"
                    else:
                        role = "Pengunjung"
                except Pengunjung.DoesNotExist:
                    role = "guest"

            user_role = role

        except Pengguna.DoesNotExist:
            role = "guest"
            user_role = "guest"
    
    # Bisa print buat cek debug
    print(f"[NAVBAR_VIEW] Username: {username} | Final Role: {role}")

    return render(request, 'accounts/navbar.html', {'user_role': user_role, 'role': role})
