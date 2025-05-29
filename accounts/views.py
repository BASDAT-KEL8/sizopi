from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegisterForm, LoginForm
from django.db import connection
import uuid

def choose_role_view(request):
    return render(request, 'accounts/choose_role.html')

def register_pengunjung_view(request):
    if request.method == 'POST':
        # Ambil data dari form POST
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']  # Masih plaintext (bisa di-hash jika mau)
        nama_depan = request.POST['nama_depan']
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST['nama_belakang']
        no_telepon = request.POST['no_telepon']
        alamat = request.POST['alamat']
        tgl_lahir = request.POST['tgl_lahir']

        try:
            with connection.cursor() as cursor:
                # Simpan ke tabel pengguna
                cursor.execute("""
                    INSERT INTO sizopi.pengguna (
                        username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    username, email, password,
                    nama_depan, nama_tengah, nama_belakang, no_telepon
                ])

                # Simpan ke tabel pengunjung
                cursor.execute("""
                    INSERT INTO sizopi.pengunjung (
                        username_p, alamat, tgl_lahir
                    ) VALUES (%s, %s, %s)
                """, [
                    username, alamat, tgl_lahir
                ])

            messages.success(request, "Registrasi berhasil! Silakan login.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat registrasi: {str(e)}")

    return render(request, 'accounts/register_pengunjung.html')

def register_staff_view(request):
    if request.method == 'POST':
        # Ambil data dari form
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']  # masih plaintext
        nama_depan = request.POST['nama_depan']
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST['nama_belakang']
        no_telepon = request.POST['no_telepon']
        role_staff = request.POST['role_staff']  # Penjaga Hewan, Pelatih Hewan, Staf Administrasi

        try:
            with connection.cursor() as cursor:
                # Simpan ke tabel pengguna
                cursor.execute("""
                    INSERT INTO sizopi.pengguna (
                        username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    username, email, password,
                    nama_depan, nama_tengah, nama_belakang, no_telepon
                ])

                # Buat UUID untuk id_staf
                id_staf = str(uuid.uuid4())

                # Tentukan tabel tujuan berdasarkan role
                if role_staff == 'Penjaga Hewan':
                    cursor.execute("""
                        INSERT INTO sizopi.penjaga_hewan (username_jh, id_staf)
                        VALUES (%s, %s)
                    """, [username, id_staf])
                elif role_staff == 'Pelatih Hewan':
                    cursor.execute("""
                        INSERT INTO sizopi.pelatih_hewan (username_lh, id_staf)
                        VALUES (%s, %s)
                    """, [username, id_staf])
                elif role_staff == 'Staf Administrasi':
                    cursor.execute("""
                        INSERT INTO sizopi.staf_admin (username_sa, id_staf)
                        VALUES (%s, %s)
                    """, [username, id_staf])
                else:
                    messages.error(request, "Role tidak dikenali.")
                    return redirect('register_staff')

            messages.success(request, "Registrasi staf berhasil! Silakan login.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat registrasi: {str(e)}")

    return render(request, 'accounts/register_staff.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']  # plaintext (belum di-hash)

            try:
                with connection.cursor() as cursor:
                    # Cari user berdasarkan email dan password
                    cursor.execute("""
                        SELECT username, nama_depan, nama_belakang 
                        FROM sizopi.pengguna
                        WHERE email = %s AND password = %s
                    """, [email, password])
                    
                    user = cursor.fetchone()

                    if user:
                        username, nama_depan, nama_belakang = user
                        request.session['email'] = email
                        request.session['nama_lengkap'] = f"{nama_depan} {nama_belakang}"
                        request.session['username'] = username
                        return redirect('dashboard')

            except Exception as e:
                messages.error(request, f"Terjadi kesalahan saat login: {str(e)}")
        else:
            messages.error(request, "Form tidak valid.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def register_dokter_view(request):
    if request.method == 'POST':
        # Ambil data dari form POST
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']  # masih plaintext
        nama_depan = request.POST['nama_depan']
        nama_tengah = request.POST.get('nama_tengah', '')
        nama_belakang = request.POST['nama_belakang']
        no_telepon = request.POST['no_telepon']
        no_str = request.POST['no_str']

        try:
            with connection.cursor() as cursor:
                # Simpan ke tabel pengguna
                cursor.execute("""
                    INSERT INTO sizopi.pengguna (
                        username, email, password, nama_depan, nama_tengah, nama_belakang, no_telepon
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [
                    username, email, password,
                    nama_depan, nama_tengah, nama_belakang, no_telepon
                ])

                # Simpan ke tabel dokter_hewan
                cursor.execute("""
                    INSERT INTO sizopi.dokter_hewan (
                        username_dh, no_str
                    ) VALUES (%s, %s)
                """, [username, no_str])

            messages.success(request, "Registrasi dokter hewan berhasil! Silakan login.")
            return redirect('login')

        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat registrasi: {str(e)}")

    return render(request, 'accounts/register_dokter.html')

def logout_view(request):
    request.session.flush()  # Clear semua session
    # messages.success(request, "Berhasil logout.")
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

def navbar_view(request):
    # 'user_role' akan otomatis tersedia dari context_processor
    return render(request, 'accounts/navbar.html')

def profile(request):
    """Profile view with proper specialization handling"""
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.session['username']
    
    with connection.cursor() as cursor:
        # Get user data
        cursor.execute("""
            SELECT username, email, nama_depan, nama_tengah, nama_belakang, no_telepon
            FROM sizopi.pengguna
            WHERE username = %s
        """, [username])
        pengguna_data = cursor.fetchone()
        
        if not pengguna_data:
            messages.error(request, "Data pengguna tidak ditemukan.")
            return redirect('login')
        
        pengguna = {
            'username': pengguna_data[0],
            'email': pengguna_data[1],
            'nama_depan': pengguna_data[2],
            'nama_tengah': pengguna_data[3],
            'nama_belakang': pengguna_data[4],
            'no_telepon': pengguna_data[5]
        }
        
        # Check user role
        role = None
        role_data = {}
        
        # Check if pengunjung
        cursor.execute("SELECT alamat, tgl_lahir FROM sizopi.pengunjung WHERE username_p = %s", [username])
        result = cursor.fetchone()
        if result:
            role = 'pengunjung'
            role_data = {'alamat': result[0], 'tgl_lahir': result[1]}
        
        # Check if dokter
        cursor.execute("SELECT no_str FROM sizopi.dokter_hewan WHERE username_dh = %s", [username])
        result = cursor.fetchone()
        if result:
            role = 'dokter'
            role_data = {'no_str': result[0]}
            
            # Get current specializations
            cursor.execute("""
                SELECT nama_spesialisasi 
                FROM sizopi.spesialisasi 
                WHERE username_sh = %s
            """, [username])
            current_spesialisasi = [row[0] for row in cursor.fetchall()]
            
            # Get all unique specializations from database
            cursor.execute("""
                SELECT DISTINCT nama_spesialisasi 
                FROM sizopi.spesialisasi
                ORDER BY nama_spesialisasi
            """)
            all_spesialisasi_db = [row[0] for row in cursor.fetchall()]
            
            # Define standard specializations
            standard_spesialisasi = [
                'Bedah Hewan',
                'Penyakit Dalam Hewan',
                'Dermatologi Hewan',
                'Kardiologi Hewan',
                'Neurologi Hewan',
                'Oftalmologi Hewan',
                'Onkologi Hewan',
                'Gizi dan Dietetik Hewan',
                'Rehabilitasi Hewan',
                'Perilaku Hewan'
            ]
            
            # Combine standard and any additional from DB
            all_spesialisasi = list(set(standard_spesialisasi))
            
            # Find "lainnya" specializations (not in standard list)
            spesialisasi_lainnya = [s for s in current_spesialisasi if s not in standard_spesialisasi]
            spesialisasi_lainnya_str = ', '.join(spesialisasi_lainnya) if spesialisasi_lainnya else ''
            
            role_data['all_spesialisasi'] = all_spesialisasi
            role_data['current_spesialisasi'] = current_spesialisasi
            role_data['spesialisasi_lainnya'] = spesialisasi_lainnya_str
        
        # Check if penjaga
        cursor.execute("SELECT id_staf FROM sizopi.penjaga_hewan WHERE username_jh = %s", [username])
        result = cursor.fetchone()
        if result:
            role = 'penjaga'
            role_data = {'id_staf': result[0]}
        
        # Check if admin
        cursor.execute("SELECT id_staf FROM sizopi.staf_admin WHERE username_sa = %s", [username])
        result = cursor.fetchone()
        if result:
            role = 'admin'
            role_data = {'id_staf': result[0]}
        
        # Check if pelatih
        cursor.execute("SELECT id_staf FROM sizopi.pelatih_hewan WHERE username_lh = %s", [username])
        result = cursor.fetchone()
        if result:
            role = 'pelatih'
            role_data = {'id_staf': result[0]}
    
    context = {
        'pengguna': pengguna,
        'role': role,
        role: role_data,
    }
    
    # Pass specialization data if dokter
    if role == 'dokter':
        context.update({
            'all_spesialisasi': role_data['all_spesialisasi'],
            'current_spesialisasi': role_data['current_spesialisasi'],
            'spesialisasi_lainnya': role_data['spesialisasi_lainnya']
        })
    
    return render(request, 'accounts/profile.html', context)


def update_profile(request):
    """Update profile with proper specialization handling"""
    if 'username' not in request.session:
        messages.error(request, "Silakan login terlebih dahulu.")
        return redirect('login')
    
    username = request.session['username']
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        with connection.cursor() as cursor:
            try:
                # Handle profile update
                if action == 'update_profile':
                    # Update basic user information
                    cursor.execute("""
                        UPDATE sizopi.pengguna 
                        SET email = %s, nama_depan = %s, nama_tengah = %s, 
                            nama_belakang = %s, no_telepon = %s
                        WHERE username = %s
                    """, [
                        request.POST.get('email', ''),
                        request.POST.get('nama_depan', ''),
                        request.POST.get('nama_tengah', ''),
                        request.POST.get('nama_belakang', ''),
                        request.POST.get('no_telepon', ''),
                        username
                    ])
                    
                    # Check if user is pengunjung and update specific data
                    cursor.execute("""
                        SELECT username_p FROM sizopi.pengunjung WHERE username_p = %s
                    """, [username])
                    
                    if cursor.fetchone():
                        tgl_lahir = request.POST.get('tgl_lahir')
                        alamat = request.POST.get('alamat', '')
                        
                        if tgl_lahir:
                            cursor.execute("""
                                UPDATE sizopi.pengunjung 
                                SET alamat = %s, tgl_lahir = %s
                                WHERE username_p = %s
                            """, [alamat, tgl_lahir, username])
                        else:
                            cursor.execute("""
                                UPDATE sizopi.pengunjung 
                                SET alamat = %s
                                WHERE username_p = %s
                            """, [alamat, username])
                    
                    # Check if user is dokter and update specializations
                    cursor.execute("""
                        SELECT username_dh FROM sizopi.dokter_hewan WHERE username_dh = %s
                    """, [username])
                    
                    if cursor.fetchone():
                        # Get selected specializations
                        selected_spesialisasi = request.POST.getlist('spesialisasi')
                        
                        # Handle "lainnya" specialization
                        if request.POST.get('spesialisasi_lainnya_check'):
                            lainnya_value = request.POST.get('spesialisasi_lainnya', '').strip()
                            if lainnya_value:
                                # Split by comma if multiple values
                                lainnya_list = [s.strip() for s in lainnya_value.split(',') if s.strip()]
                                selected_spesialisasi.extend(lainnya_list)
                        
                        # Remove duplicates
                        selected_spesialisasi = list(set(selected_spesialisasi))
                        
                        # Delete all existing specializations
                        cursor.execute("""
                            DELETE FROM sizopi.spesialisasi 
                            WHERE username_sh = %s
                        """, [username])
                        
                        # Insert new specializations
                        for spec in selected_spesialisasi:
                            if spec:  # Only insert non-empty values
                                cursor.execute("""
                                    INSERT INTO sizopi.spesialisasi (username_sh, nama_spesialisasi)
                                    VALUES (%s, %s)
                                """, [username, spec])
                    
                    messages.success(request, "Profil berhasil diperbarui.")
                
                # Handle password change
                elif action == 'change_password':
                    password_lama = request.POST.get('password_lama')
                    password_baru = request.POST.get('password_baru')
                    konfirmasi_password = request.POST.get('konfirmasi_password')
                    
                    # Verify old password
                    cursor.execute("""
                        SELECT username FROM sizopi.pengguna 
                        WHERE username = %s AND password = %s
                    """, [username, password_lama])
                    
                    if not cursor.fetchone():
                        messages.error(request, "Password lama tidak sesuai.")
                        return redirect('profile')
                    
                    # Check if new password and confirmation match
                    if password_baru != konfirmasi_password:
                        messages.error(request, "Password baru dan konfirmasi tidak cocok.")
                        return redirect('profile')
                    
                    # Update password
                    cursor.execute("""
                        UPDATE sizopi.pengguna 
                        SET password = %s 
                        WHERE username = %s
                    """, [password_baru, username])
                    
                    messages.success(request, "Password berhasil diubah.")
                    
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan: {str(e)}")
                return redirect('profile')
        
    return redirect('profile')

def get_complete_user_data(username):
    with connection.cursor() as cursor:
        # Get basic user data
        cursor.execute("""
            SELECT username, email, nama_depan, nama_tengah, nama_belakang, no_telepon
            FROM sizopi.pengguna 
            WHERE username = %s
        """, [username])
        
        user_row = cursor.fetchone()
        if not user_row:
            return None
        
        user_data = {
            'pengguna': {
                'username': user_row[0],
                'email': user_row[1],
                'nama_depan': user_row[2],
                'nama_tengah': user_row[3],
                'nama_belakang': user_row[4],
                'no_telepon': user_row[5]
            }
        }
        
        
        # Check Dokter Hewan
        cursor.execute("SELECT no_str FROM sizopi.dokter_hewan WHERE username_dh = %s", [username])
        dokter_row = cursor.fetchone()
        if dokter_row:
            user_data['role'] = 'dokter'
            user_data['dokter'] = {
                'no_str': dokter_row[0]
            }
            
            # Get specializations
            cursor.execute("""
                SELECT nama_spesialisasi 
                FROM sizopi.spesialisasi 
                WHERE username_sh = %s
            """, [username])
            specializations = [spec[0] for spec in cursor.fetchall()]
            user_data['dokter']['spesialisasi'] = ', '.join(specializations)
            return user_data
        
        # Check Penjaga Hewan
        cursor.execute("SELECT id_staf FROM sizopi.penjaga_hewan WHERE username_jh = %s", [username])
        penjaga_row = cursor.fetchone()
        if penjaga_row:
            user_data['role'] = 'penjaga'
            user_data['penjaga'] = {
                'id_staf': penjaga_row[0]
            }
            return user_data
        
        # Check Pelatih Hewan
        cursor.execute("SELECT id_staf FROM sizopi.pelatih_hewan WHERE username_lh = %s", [username])
        pelatih_row = cursor.fetchone()
        if pelatih_row:
            user_data['role'] = 'pelatih'
            user_data['pelatih'] = {
                'id_staf': pelatih_row[0]
            }
            return user_data
        
        # Check Staf Admin
        cursor.execute("SELECT id_staf FROM sizopi.staf_admin WHERE username_sa = %s", [username])
        admin_row = cursor.fetchone()
        if admin_row:
            user_data['role'] = 'admin'
            user_data['admin'] = {
                'id_staf': admin_row[0]
            }
            return user_data
        
        # Check Pengunjung
        cursor.execute("SELECT alamat, tgl_lahir FROM sizopi.pengunjung WHERE username_p = %s", [username])
        pengunjung_row = cursor.fetchone()
        if pengunjung_row:
            user_data['role'] = 'pengunjung'
            user_data['pengunjung'] = {
                'alamat': pengunjung_row[0],
                'tgl_lahir': pengunjung_row[1]
            }
            
            # Check if adopter
            cursor.execute("""
                SELECT 1 FROM sizopi.adopter 
                WHERE username_adopter = %s
            """, [username])
            if cursor.fetchone():
                user_data['role'] = 'pengunjung_adopter'
            
            return user_data
        
        # Default role
        user_data['role'] = 'unknown'
        return user_data

def get_user_role_simple(username):
    if not username:
        return 'guest'
    
    with connection.cursor() as cursor:
        # Cek role berurutan - sama seperti context processor
        cursor.execute("SELECT 1 FROM sizopi.dokter_hewan WHERE username_dh = %s", [username])
        if cursor.fetchone():
            return 'Dokter Hewan'
        
        cursor.execute("SELECT 1 FROM sizopi.penjaga_hewan WHERE username_jh = %s", [username])
        if cursor.fetchone():
            return 'Penjaga Hewan'
        
        cursor.execute("SELECT 1 FROM sizopi.pelatih_hewan WHERE username_lh = %s", [username])
        if cursor.fetchone():
            return 'Staf Pelatih Pertunjukan'
        
        cursor.execute("SELECT 1 FROM sizopi.staf_admin WHERE username_sa = %s", [username])
        if cursor.fetchone():
            return 'Staf Administrasi'
        
        cursor.execute("SELECT 1 FROM sizopi.pengunjung WHERE username_p = %s", [username])
        if cursor.fetchone():
            cursor.execute("""
                SELECT 1 FROM sizopi.adopter 
                WHERE username_adopter = %s
            """, [username])
            if cursor.fetchone():
                return 'pengunjung_adopter'
            else:
                return 'Pengunjung'
    
    return 'guest'

def check_user_permission(username, required_roles):
    user_role = get_user_role_simple(username)
    return user_role in required_roles

def validate_user_data(post_data):
    errors = []
    
    email = post_data.get('email', '').strip()
    nama_depan = post_data.get('nama_depan', '').strip()
    nama_belakang = post_data.get('nama_belakang', '').strip()
    no_telepon = post_data.get('no_telepon', '').strip()
    
    if not email:
        errors.append('Email tidak boleh kosong')
    if not nama_depan:
        errors.append('Nama depan tidak boleh kosong')
    if not nama_belakang:
        errors.append('Nama belakang tidak boleh kosong')
    if not no_telepon:
        errors.append('Nomor telepon tidak boleh kosong')
    
    return errors