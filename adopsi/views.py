from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta, datetime
import uuid
from django.db import connection

# @login_required
def detail_hewan(request, hewan_id):
    """Menampilkan detail hewan untuk admin"""
    # Cek apakah user adalah admin
    # FIXED: Check session authentication
    if 'username' not in request.session:
        messages.error(request, "Anda harus login untuk mengakses halaman admin.")
        return redirect('login')

    username = request.session['username']

    # Check admin using session username
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_sa FROM sizopi.staf_admin
                WHERE username_sa = %s
            """, [username])
            admin_data = cursor.fetchone()
        
        if not admin_data:
            messages.error(request, f"Username '{username}' tidak memiliki izin untuk menghapus adopsi.")
            return redirect('adopsi:admin_dashboard')
            
    except Exception as e:
        messages.error(request, f"Error verifying admin access: {str(e)}")
        return redirect('adopsi:admin_dashboard')

    # Ambil data hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM sizopi.hewan 
            WHERE id = %s
        """, [hewan_id])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Hewan tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')
    
    # Buat dictionary untuk hewan
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'nama_habitat': hewan_data[6],
        'url_foto': hewan_data[7]
    }
    
    # Ambil status adopsi hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.id_adopter, a.id_hewan, a.status_pembayaran, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial
            FROM sizopi.adopsi a
            WHERE a.id_hewan = %s AND a.tgl_berhenti_adopsi > %s
            ORDER BY a.tgl_mulai_adopsi DESC
            LIMIT 1
        """, [hewan_id, timezone.now().date()])
        current_adoption = cursor.fetchone()
    
    if not current_adoption:
        messages.error(request, "Hewan ini belum diadopsi.")
        return redirect('adopsi:admin_dashboard')

    class AdoptionObject:
        pass

    adoption = AdoptionObject()
    adoption.id_hewan = hewan
    adoption.status_adopsi = current_adoption[2]  
    adoption.tgl_mulai_adopsi = current_adoption[3] 
    adoption.tgl_berhenti_adopsi = current_adoption[4] 
    adoption.kontribusi_finansial = current_adoption[5]

    # Cek data adopter
    id_adopter = current_adoption[0]
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, username_adopter, total_kontribusi
            FROM sizopi.adopter 
            WHERE id_adopter = %s
        """, [id_adopter])
        adopter_data = cursor.fetchone()

    if not adopter_data:
        messages.error(request, "Data adopter tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')

    # Buat dictionary untuk adopter
    adopter = {
        'id_adopter': adopter_data[0],
        'username_adopter': adopter_data[1],
        'total_kontribusi': adopter_data[2]
    }

    # Cek tipe adopter (individu atau organisasi)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, nik, nama
            FROM sizopi.individu
            WHERE id_adopter = %s
        """, [id_adopter])
        individu_data = cursor.fetchone()
    
    if individu_data:
        adopter_type = 'individu'
        adopter_detail = {
            'id_adopter': individu_data[0],
            'nik': individu_data[1],
            'nama': individu_data[2]
        }
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter, npp, nama_organisasi
                FROM sizopi.organisasi
                WHERE id_adopter = %s
            """, [id_adopter])
            organisasi_data = cursor.fetchone()
        
        if organisasi_data:
            adopter_type = 'organisasi'
            adopter_detail = {
                'id_adopter': organisasi_data[0],
                'npp': organisasi_data[1],
                'nama_organisasi': organisasi_data[2]
            }
        else:
            adopter_type = 'unknown'
            adopter_detail = None

    context = {
        'adoption': adoption,
        'hewan': hewan,
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': adoption.tgl_mulai_adopsi.strftime('%Y-%m-%d'),
    }

    return render(request, 'adopsi/detail_hewan.html', context)

# @login_required
def adopt_hewan(request, hewan_id):
    """Form pendaftaran adopsi hewan"""
    # Ambil data hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM sizopi.hewan 
            WHERE id = %s
        """, [hewan_id])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Hewan tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')
    
    # Buat dictionary untuk hewan
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'nama_habitat': hewan_data[6],
        'url_foto': hewan_data[7]
    }
    
    # Cek apakah hewan sudah diadopsi
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sizopi.adopsi 
            WHERE id_hewan = %s AND tgl_berhenti_adopsi > %s
        """, [hewan_id, timezone.now().date()])
        is_adopted = cursor.fetchone()[0] > 0
    
    if is_adopted:
        messages.error(request, f"Hewan ini sudah diadopsi oleh orang lain.")
        return redirect('adopsi:detail_hewan', hewan_id=hewan_id)
    
    # Cek apakah user sudah punya akun Pengunjung
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT username_p, alamat, tgl_lahir
            FROM sizopi.pengunjung
            WHERE username_p = %s
        """, [request.user.username])
        pengunjung_data = cursor.fetchone()
    
    if not pengunjung_data:
        messages.error(request, "Anda harus memiliki akun pengunjung untuk mengadopsi hewan.")
        return redirect('profile_update')
    
    pengunjung = {
        'username_p': pengunjung_data[0],  # Indeks dimulai dari 0, bukan 1
        'alamat': pengunjung_data[1],
        'tgl_lahir': pengunjung_data[2] if len(pengunjung_data) > 2 else None
    }
    
    if request.method == 'POST':
        form = AdopsiForm(request.POST)
        if form.is_valid():
            # Cek atau buat Adopter
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id_adopter, username_adopter, total_kontribusi 
                    FROM sizopi.adopter 
                    WHERE username_adopter = %s
                """, [pengunjung['username_p']])  
                adopter_data = cursor.fetchone()
            
            if not adopter_data:
                # Buat adopter baru
                new_adopter_id = uuid.uuid4()
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO sizopi.adopter 
                        (id_adopter, username_adopter, total_kontribusi) 
                        VALUES (%s, %s, %s)
                        RETURNING id_adopter
                    """, [new_adopter_id, pengunjung['username_p'], 0])  # Gunakan username_p
                    adopter_id = cursor.fetchone()[0]
            else:
                adopter_id = adopter_data[0]
            
            # Proses tipe adopter (individu atau organisasi)
            adopter_type = form.cleaned_data['adopter_type']
            if adopter_type == 'individu':
                # Cek apakah sudah ada data individu
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id_adopter, nik, nama 
                        FROM sizopi.individu 
                        WHERE id_adopter = %s
                    """, [adopter_id])
                    individu_data = cursor.fetchone()
                
                if individu_data:
                    # Update data individu
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE sizopi.individu 
                            SET nik = %s, nama = %s 
                            WHERE id_adopter = %s
                        """, [form.cleaned_data['nik'], form.cleaned_data['nama'], adopter_id])
                else:
                    # Buat data individu baru
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO sizopi.individu 
                            (id_adopter, nik, nama) 
                            VALUES (%s, %s, %s)
                        """, [adopter_id, form.cleaned_data['nik'], form.cleaned_data['nama']])
            else:
                # Cek apakah sudah ada data organisasi
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id_adopter, npp, nama_organisasi 
                        FROM sizopi.organisasi 
                        WHERE id_adopter = %s
                    """, [adopter_id])
                    organisasi_data = cursor.fetchone()
                
                if organisasi_data:
                    # Update data organisasi
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE sizopi.organisasi 
                            SET npp = %s, nama_organisasi = %s 
                            WHERE id_adopter = %s
                        """, [form.cleaned_data['npp'], form.cleaned_data['nama'], adopter_id])
                else:
                    # Buat data organisasi baru
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO sizopi.organisasi 
                            (id_adopter, npp, nama_organisasi) 
                            VALUES (%s, %s, %s)
                        """, [adopter_id, form.cleaned_data['npp'], form.cleaned_data['nama']])
            
            # Hitung tanggal akhir adopsi
            tgl_mulai = timezone.now().date()
            periode_bulan = form.cleaned_data['periode']
            tgl_akhir = tgl_mulai + timedelta(days=30 * periode_bulan)
            
            # Simpan data adopsi
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sizopi.adopsi 
                    (id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id_adopter, id_hewan, tgl_mulai_adopsi
                """, [adopter_id, hewan_id, 'Tertunda', tgl_mulai, tgl_akhir, form.cleaned_data['kontribusi']])
                adopsi_info = cursor.fetchone()
            
            # Update total kontribusi adopter akan ditangani oleh trigger
            # saat status_pembayaran menjadi 'Lunas'
            
            messages.success(request, f"Terima kasih! Anda telah berhasil mengadopsi {hewan['nama']}.")
            return redirect('adopsi:detail_adopsi', id_adopter=adopter_id, id_hewan=hewan_id, tgl_mulai_adopsi=tgl_mulai.strftime('%Y-%m-%d'))
    else:
        form = AdopsiForm(initial={'kontribusi': 500000, 'periode': 3})
    
    context = {
        'hewan': hewan,
        'form': form,
    }
    return render(request, 'adopsi/adopt_form.html', context)

def dashboard_adopter(request):
    # Ambil data pengunjung dan adopter
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_p, alamat, tgl_lahir
                FROM sizopi.pengunjung p
                JOIN sizopi.pengguna u ON p.username_p = u.username
                WHERE u.username = %s
            """, [request.session['username']])
            pengunjung_data = cursor.fetchone()
        
        if not pengunjung_data:
            messages.error(request, "Anda belum terdaftar sebagai pengunjung.")
        
        pengunjung = {
            'username_p': pengunjung_data[0],
            'alamat': pengunjung_data[1],
            'tgl_lahir': pengunjung_data[2]
        }
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter, username_adopter, total_kontribusi
                FROM sizopi.adopter
                WHERE username_adopter = %s
            """, [pengunjung['username_p']])  # Gunakan username_p
            adopter_data = cursor.fetchone()
        
        if not adopter_data:
            messages.error(request, "Anda belum terdaftar sebagai adopter.")
        
        adopter = {
            'id_adopter': adopter_data[0],
            'username_adopter': {
                'username_p': {
                    'username': pengunjung['username_p'],
                    'email': request.session.get('email', f"{pengunjung['username_p']}@example.com")
                }
            },
            'total_kontribusi': adopter_data[2],
            'jenis_adopter': 'individu',  # default
        }
        
        # Ambil data adopsi
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.id_adopter, h.id, h.nama, h.spesies, h.url_foto,
                    a.status_pembayaran, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial
                FROM sizopi.adopsi a
                JOIN sizopi.hewan h ON a.id_hewan = h.id
                WHERE a.id_adopter = %s
                ORDER BY a.tgl_mulai_adopsi DESC
            """, [adopter['id_adopter']])
            adoption_rows = cursor.fetchall()
        
        adoptions = []
        active_adoptions_count = 0  # Counter untuk adopsi aktif
        current_date = timezone.now().date()  # Tanggal sekarang
        
        for row in adoption_rows:
            adoption_data = {
                'id_adopter__id_adopter': row[0],
                'id_hewan__id': row[1],
                'id_hewan__nama': row[2],
                'id_hewan__spesies': row[3],
                'id_hewan__url_foto': {'url': row[4]} if row[4] else {'url': '/static/images/placeholder.jpg'},
                'status_pembayaran': row[5],
                'tgl_mulai_adopsi': row[6],
                'tgl_mulai_adopsi_str': row[6].strftime('%Y-%m-%d') if row[6] else '',
                'tgl_berhenti_adopsi': row[7],
                'kontribusi_finansial': row[8],
            }
            
            # Cek apakah adopsi masih aktif
            if row[7] and row[7] >= current_date:  # tgl_berhenti_adopsi >= tanggal sekarang
                active_adoptions_count += 1
            
            adoptions.append(adoption_data)
        
        context = {
            'adopter': adopter,
            'adoptions': adoptions,
            'active_adoptions': active_adoptions_count,  # Tambahkan counter adopsi aktif
            'now': timezone.now(),
        }
        return render(request, 'adopsi/dashboard_adopter.html', context)
    
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan: {str(e)}")
        return redirect('adopsi:dashboard_adopter')  # Tambahkan redirect untuk error handling
    
# @login_required
def detail_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Menampilkan detail adopsi untuk adopter (user)"""
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')

    # Ambil data adopter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, username_adopter, total_kontribusi
            FROM sizopi.adopter
            WHERE id_adopter = %s
        """, [id_adopter])
        adopter_data = cursor.fetchone()
    
    if not adopter_data:
        messages.error(request, "Data adopter tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    adopter = {
        'id_adopter': adopter_data[0],
        'username_adopter': adopter_data[1],
        'total_kontribusi': adopter_data[2]
    }
    
    # Ambil data hewan - dengan deskripsi dan kebutuhan khusus
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, 
                   nama_habitat, url_foto
            FROM sizopi.hewan
            WHERE id = %s
        """, [id_hewan])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Data hewan tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    # Handle URL foto dengan benar
    foto_url = hewan_data[7] if hewan_data[7] else '/static/images/placeholder.jpg'
    if foto_url and not foto_url.startswith(('http', '/static', '/media')):
        foto_url = f'/media/{foto_url}'
    
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'nama_habitat': hewan_data[6],
        'url_foto': foto_url,  # LANGSUNG URL STRING, BUKAN OBJECT
    }
    
    # Ambil data adopsi
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, 
                   tgl_berhenti_adopsi, kontribusi_finansial
            FROM sizopi.adopsi
            WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
        """, [id_adopter, id_hewan, tgl_mulai])
        adopsi_data = cursor.fetchone()
    
    if not adopsi_data:
        messages.error(request, "Adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    # Buat object adopsi dengan nested objects untuk consistency
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.id_adopter = adopter
    adopsi.id_hewan = hewan
    adopsi.status_pembayaran = adopsi_data[2]
    adopsi.tgl_mulai_adopsi = adopsi_data[3]
    adopsi.tgl_berhenti_adopsi = adopsi_data[4]
    adopsi.kontribusi_finansial = adopsi_data[5]

    # Cek tipe adopter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, nik, nama
            FROM sizopi.individu
            WHERE id_adopter = %s
        """, [id_adopter])
        individu_data = cursor.fetchone()
    
    if individu_data:
        adopter_type = 'individu'
        adopter_detail = {
            'id_adopter': individu_data[0],
            'nik': individu_data[1],
            'nama': individu_data[2]
        }
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter, npp, nama_organisasi
                FROM sizopi.organisasi
                WHERE id_adopter = %s
            """, [id_adopter])
            organisasi_data = cursor.fetchone()
        
        if organisasi_data:
            adopter_type = 'organisasi'
            adopter_detail = {
                'id_adopter': organisasi_data[0],
                'npp': organisasi_data[1],
                'nama_organisasi': organisasi_data[2]
            }
        else:
            adopter_type = 'unknown'
            adopter_detail = None
    
    # Ambil data pengunjung
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.username_p, p.alamat, p.tgl_lahir
            FROM sizopi.pengunjung p
            JOIN sizopi.adopter a ON p.username_p = a.username_adopter
            WHERE a.id_adopter = %s
        """, [id_adopter])
        pengunjung_data = cursor.fetchone()
    
    pengunjung = None
    if pengunjung_data:
        pengunjung = {
            'username_p': pengunjung_data[0],
            'alamat': pengunjung_data[1],
            'tgl_lahir': pengunjung_data[2]
        }

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung': pengunjung,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': adopsi.tgl_mulai_adopsi.strftime('%Y-%m-%d'),
    }

    return render(request, 'adopsi/detail_adopsi.html', context)


def perpanjang_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    # Ambil data adopter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, username_adopter, total_kontribusi
            FROM sizopi.adopter
            WHERE id_adopter = %s
        """, [id_adopter])
        adopter_data = cursor.fetchone()
    
    if not adopter_data:
        messages.error(request, "Data adopter tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    adopter = {
        'id_adopter': adopter_data[0],
        'username_adopter': adopter_data[1],
        'total_kontribusi': adopter_data[2]
    }
    
    # Ambil data hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM sizopi.hewan
            WHERE id = %s
        """, [id_hewan])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Data hewan tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'nama_habitat': hewan_data[6],
        'url_foto': hewan_data[7]
    }
    
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')
    
    # Ambil data adopsi
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
            FROM sizopi.adopsi
            WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
        """, [id_adopter, id_hewan, tgl_mulai])
        adopsi_data = cursor.fetchone()
    
    if not adopsi_data:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    # Dummy adopsi
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.status_pembayaran = adopsi_data[2]
    adopsi.tgl_mulai_adopsi = adopsi_data[3]
    adopsi.tgl_berhenti_adopsi = adopsi_data[4]
    adopsi.kontribusi_finansial = adopsi_data[5]

    if request.method == 'POST':
        periode_bulan = int(request.POST.get('periode'))
        kontribusi = int(request.POST.get('kontribusi'))

        # Update adopsi dengan SQL
        new_tgl_berhenti = adopsi.tgl_berhenti_adopsi + timezone.timedelta(days=30 * periode_bulan)
        new_kontribusi = adopsi.kontribusi_finansial + kontribusi
        
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE sizopi.adopsi
                SET tgl_berhenti_adopsi = %s, kontribusi_finansial = %s, status_pembayaran = 'Tertunda'
                WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
            """, [new_tgl_berhenti, new_kontribusi, id_adopter, id_hewan, tgl_mulai])
        
        # Update total_kontribusi akan ditangani oleh trigger ketika status_pembayaran diubah menjadi 'Lunas'

        messages.success(request, f"Adopsi {hewan['nama']} berhasil diperpanjang.")
        return redirect('adopsi:dashboard_adopter')

    context = {
        'adopsi': adopsi,
        'hewan': hewan,
    }
    return render(request, 'adopsi/perpanjang_form.html', context)

# @login_required
def berhenti_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Berhenti adopsi"""
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')

    # Ambil data adopsi
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.status_pembayaran, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial
            FROM sizopi.adopsi a
            JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
            WHERE ad.id_adopter = %s AND a.id_hewan = %s AND a.tgl_mulai_adopsi = %s
        """, [id_adopter, id_hewan, tgl_mulai])
        adopsi_data = cursor.fetchone()
    
    if not adopsi_data:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')

    # Dummy adopsi buat template
    class AdopsiObject:
        pass

    adopsi = AdopsiObject()
    adopsi.status_pembayaran = adopsi_data[0]
    adopsi.tgl_mulai_adopsi = adopsi_data[1]
    adopsi.tgl_berhenti_adopsi = adopsi_data[2]
    adopsi.kontribusi_finansial = adopsi_data[3]

    # Ambil data hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM sizopi.hewan
            WHERE id = %s
        """, [id_hewan])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Data hewan tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'nama_habitat': hewan_data[6],
        'url_foto': hewan_data[7]
    }

    # Ambil data adopter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, username_adopter, total_kontribusi
            FROM sizopi.adopter
            WHERE id_adopter = %s
        """, [id_adopter])
        adopter_data = cursor.fetchone()
    
    adopter = {
        'id_adopter': adopter_data[0],
        'username_adopter': adopter_data[1],
        'total_kontribusi': adopter_data[2]
    } if adopter_data else {}

    # Cek tipe adopter (individu atau organisasi)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, nik, nama
            FROM sizopi.individu
            WHERE id_adopter = %s
        """, [id_adopter])
        individu_data = cursor.fetchone()
    
    if individu_data:
        adopter_type = 'individu'
        adopter_detail = {
            'id_adopter': individu_data[0],
            'nik': individu_data[1],
            'nama': individu_data[2]
        }
    else:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter, npp, nama_organisasi
                FROM sizopi.organisasi
                WHERE id_adopter = %s
            """, [id_adopter])
            organisasi_data = cursor.fetchone()
        
        if organisasi_data:
            adopter_type = 'organisasi'
            adopter_detail = {
                'id_adopter': organisasi_data[0],
                'npp': organisasi_data[1],
                'nama_organisasi': organisasi_data[2]
            }
        else:
            adopter_type = 'unknown'
            adopter_detail = None

    # Ambil data pengunjung
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.username_p, p.alamat, p.tgl_lahir
            FROM sizopi.pengunjung p
            JOIN sizopi.adopter a ON p.username_p = a.username_adopter
            WHERE a.id_adopter = %s
        """, [id_adopter])
        pengunjung_data = cursor.fetchone()
    
    pengunjung = None
    if pengunjung_data:
        pengunjung = {
            'username_p': pengunjung_data[0],
            'alamat': pengunjung_data[1],
            'tgl_lahir': pengunjung_data[2]
        }

    if request.method == 'POST':
        # Update tanggal berhenti adopsi menjadi hari ini
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE sizopi.adopsi
                SET tgl_berhenti_adopsi = CURRENT_DATE
                WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
            """, [id_adopter, id_hewan, tgl_mulai])
        
        # Cek apakah user adalah admin
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM sizopi.staf_admin
                WHERE username_sa = %s
            """, [request.user.username])
            is_admin = cursor.fetchone() is not None
        
        messages.success(request, "Adopsi berhasil dihentikan.")

        # FIXED: Ganti URL redirect ke yang pasti ada
        if is_admin:
            return redirect('adopsi:admin_dashboard')  # Ganti dari admin_daftar_adopsi
        else:
            return redirect('adopsi:admin_dashboard')  # Temporary, nanti bisa ganti ke dashboard_adopter kalau sudah fix

    # FIXED: Buat structure yang match dengan template expectations
    # Template expect adopsi.id_hewan.nama, adopsi.id_hewan.spesies, dll
    adopsi.id_hewan = type('HewanObj', (), hewan)()
    
    context = {
        'adopsi': adopsi,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung': pengunjung,
        'now': timezone.now(),
        'back_url': request.META.get('HTTP_REFERER', 'javascript:history.back()')
    }
    return render(request, 'adopsi/berhenti_adopsi.html', context)

def admin_daftar_hewan(request):
    # FIXED: Check session authentication
    if 'username' not in request.session:
        messages.error(request, "Anda harus login untuk mengakses halaman admin.")
        return redirect('login')

    username = request.session['username']

    # Check admin using session username
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_sa FROM sizopi.staf_admin
                WHERE username_sa = %s
            """, [username])
            admin_data = cursor.fetchone()
        
        if not admin_data:
            messages.error(request, f"Username '{username}' tidak memiliki izin untuk menghapus adopsi.")
            return redirect('adopsi:admin_dashboard')
            
    except Exception as e:
        messages.error(request, f"Error verifying admin access: {str(e)}")
        return redirect('adopsi:admin_dashboard')
    
    # Get filter parameters
    status_filter = request.GET.get('status', None)
    species_filter = request.GET.get('species', None)
    
    # Base query
    base_query = "SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto FROM sizopi.hewan"
    count_query = "SELECT COUNT(*) FROM sizopi.hewan"
    
    # Get adopted animal IDs
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT id_hewan FROM sizopi.adopsi
            WHERE tgl_berhenti_adopsi > %s
        """, [timezone.now().date()])
        adopted_animal_ids = [row[0] for row in cursor.fetchall()]
    
    # Build WHERE clause based on filters
    where_clauses = []
    params = []
    
    if status_filter == 'diadopsi' and adopted_animal_ids:
        placeholders = ', '.join(['%s'] * len(adopted_animal_ids))
        where_clauses.append(f"id IN ({placeholders})")
        params.extend(adopted_animal_ids)
    elif status_filter == 'available' and adopted_animal_ids:
        placeholders = ', '.join(['%s'] * len(adopted_animal_ids))
        where_clauses.append(f"id NOT IN ({placeholders})")
        params.extend(adopted_animal_ids)
    
    if species_filter:
        where_clauses.append("spesies ILIKE %s")
        params.append(f"%{species_filter}%")
    
    # Combine WHERE clauses
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
        count_query += " WHERE " + " AND ".join(where_clauses)
    
    # Order by
    base_query += " ORDER BY nama"
    
    # Count total items for pagination
    with connection.cursor() as cursor:
        cursor.execute(count_query, params)
        total_items = cursor.fetchone()[0]
    
    # Pagination
    items_per_page = 12
    page_number = request.GET.get('page', 1)
    try:
        page_number = int(page_number)
    except ValueError:
        page_number = 1
    
    # Calculate offset
    offset = (page_number - 1) * items_per_page
    
    # Add LIMIT and OFFSET to query
    base_query += " LIMIT %s OFFSET %s"
    params.extend([items_per_page, offset])
    
    # Execute query
    with connection.cursor() as cursor:
        cursor.execute(base_query, params)
        animals_data = cursor.fetchall()
    
    # Process animal data
    animals = []
    for animal_row in animals_data:
        animal = {
            'id': animal_row[0],
            'nama': animal_row[1],
            'spesies': animal_row[2],
            'asal_hewan': animal_row[3],
            'tanggal_lahir': animal_row[4],
            'status_kesehatan': animal_row[5],
            'nama_habitat': animal_row[6],
            'url_foto': animal_row[7]
        }
        animals.append(animal)
    
    # Get distinct species for filter dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT spesies FROM sizopi.hewan")
        distinct_species = [row[0] for row in cursor.fetchall()]
    
    # Create a paginator object
    total_pages = (total_items + items_per_page - 1) // items_per_page
    has_previous = page_number > 1
    has_next = page_number < total_pages
    
    # Manually create a paginator-like object
    page_obj = {
        'object_list': animals,
        'number': page_number,
        'has_previous': has_previous,
        'has_next': has_next,
        'previous_page_number': page_number - 1 if has_previous else None,
        'next_page_number': page_number + 1 if has_next else None,
        'paginator': {
            'num_pages': total_pages,
            'count': total_items,
            'page_range': range(1, total_pages + 1)
        }
    }
    
    context = {
        'animals': page_obj,
        'status_filter': status_filter,
        'species_filter': species_filter,
        'distinct_species': distinct_species,
        'adopted_animal_ids': adopted_animal_ids,
    }
    return render(request, 'adopsi/admin/daftar_hewan.html', context)

# @login_required
def admin_detail_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Menampilkan detail adopsi untuk admin"""
    # Cek apakah user adalah admin
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sizopi.staf_admin 
            WHERE username_sa = %s
        """, [request.user.username])
        is_admin = cursor.fetchone() is not None
    
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:admin_dashboard')
    
    # Ambil data adopter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, username_adopter, total_kontribusi
            FROM sizopi.adopter
            WHERE id_adopter = %s
        """, [id_adopter])
        adopter_data = cursor.fetchone()
    
    if not adopter_data:
        messages.error(request, "Data adopter tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')
    
    adopter = {
        'id_adopter': adopter_data[0],
        'username_adopter': adopter_data[1],
        'total_kontribusi': adopter_data[2]
    }
    
    # Ambil data hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM sizopi.hewan
            WHERE id = %s
        """, [id_hewan])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Data hewan tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')
    
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'nama_habitat': hewan_data[6],
        'url_foto': hewan_data[7]
    }
    
    # Ambil data adopsi
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
            FROM sizopi.adopsi
            WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
        """, [id_adopter, id_hewan, tgl_mulai])
        adopsi_data = cursor.fetchone()
    
    if not adopsi_data:
        messages.error(request, "Adopsi tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')
    
    # Create dummy adopsi object for template
    class AdopsiObject:
        pass
    
    adopsi = AdopsiObject()
    adopsi.id_adopter = adopter
    adopsi.id_hewan = hewan
    adopsi.status_pembayaran = adopsi_data[2]
    adopsi.tgl_mulai_adopsi = adopsi_data[3]
    adopsi.tgl_berhenti_adopsi = adopsi_data[4]
    adopsi.kontribusi_finansial = adopsi_data[5]
    
    # Cek tipe adopter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, nik, nama
            FROM sizopi.individu
            WHERE id_adopter = %s
        """, [id_adopter])
        individu_data = cursor.fetchone()
    
    if individu_data:
        adopter_type = 'individu'
        adopter_detail = {
            'id_adopter': individu_data[0],
            'nik': individu_data[1],
            'nama': individu_data[2]
        }
    else:

        with connection.cursor() as cursor:
           cursor.execute("""
               SELECT id_adopter, npp, nama_organisasi
               FROM sizopi.organisasi
               WHERE id_adopter = %s
           """, [id_adopter])
           organisasi_data = cursor.fetchone()
       
        if organisasi_data:
           adopter_type = 'organisasi'
           adopter_detail = {
               'id_adopter': organisasi_data[0],
               'npp': organisasi_data[1],
               'nama_organisasi': organisasi_data[2]
           }
        else:
           adopter_type = 'unknown'
           adopter_detail = None
   
   # Ambil data pengunjung
    with connection.cursor() as cursor:
       cursor.execute("""
           SELECT p.username_p, p.alamat
           FROM sizopi.pengunjung p
           JOIN sizopi.adopter a ON p.username_p = a.username_adopter
           WHERE a.id_adopter = %s
       """, [id_adopter])
       pengunjung_data = cursor.fetchone()
   
    pengunjung = None
    if pengunjung_data:
       pengunjung = {
           'username_p': pengunjung_data[0],
           'alamat': pengunjung_data[1]
       }
   
    context = {
       'adopsi': adopsi,
       'hewan': hewan,
       'adopter': adopter,
       'adopter_type': adopter_type,
       'adopter_detail': adopter_detail,
       'pengunjung': pengunjung,
       'now': timezone.now(),
       'tgl_mulai_adopsi_str': adopsi.tgl_mulai_adopsi.strftime('%Y-%m-%d'),
   }
   
    return render(request, 'adopsi/admin/detail_adopsi.html', context)
# FIX admin_proses_adopsi

def admin_proses_adopsi(request, hewan_id):
    """Form pendaftaran adopsi hewan oleh admin - FIXED"""
    
    # FIXED: Session auth check
    if 'username' not in request.session:
        messages.error(request, "Anda harus login untuk mengakses halaman admin.")
        return redirect('login')
    
    username = request.session['username']
    
    # Check admin status
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_sa FROM sizopi.staf_admin 
                WHERE username_sa = %s
            """, [username])
            admin_data = cursor.fetchone()
        
        if not admin_data:
            messages.error(request, f"Username '{username}' tidak memiliki akses admin.")
            return redirect('adopsi:admin_dashboard')
            
    except Exception as e:
        messages.error(request, f"Error verifying admin access: {str(e)}")
        return redirect('adopsi:admin_dashboard')
    
    # Ambil data hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM sizopi.hewan
            WHERE id = %s
        """, [hewan_id])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Data hewan tidak ditemukan.")
        return redirect('adopsi:admin_daftar_hewan')
    
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'nama_habitat': hewan_data[6],
        'url_foto': hewan_data[7]
    }
    
    # Cek apakah hewan sudah diadopsi
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sizopi.adopsi 
            WHERE id_hewan = %s AND tgl_berhenti_adopsi > CURRENT_DATE
        """, [hewan_id])
        is_adopted = cursor.fetchone()[0] > 0
    
    if is_adopted:
        messages.error(request, f"Hewan ini sudah diadopsi oleh orang lain.")
        return redirect('adopsi:admin_daftar_hewan')
    
    if request.method == 'POST':
        # Get username from form
        username_form = request.POST.get('username')
        
        # Cek apakah username ada
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_p, alamat, tgl_lahir
                FROM sizopi.pengunjung
                WHERE username_p = %s
            """, [username_form])
            pengunjung_data = cursor.fetchone()
        
        if not pengunjung_data:
            messages.error(request, "Akun pengunjung tidak ditemukan.")
            return redirect('adopsi:admin_proses_adopsi', hewan_id=hewan_id)
        
        pengunjung = {
            'username_p': pengunjung_data[0],  
            'alamat': pengunjung_data[1],
            'tgl_lahir': pengunjung_data[2]
        }
        
        # Cek atau buat Adopter
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter, username_adopter, total_kontribusi
                FROM sizopi.adopter
                WHERE username_adopter = %s
            """, [pengunjung['username_p']])  
            adopter_data = cursor.fetchone()
        
        if not adopter_data:
            # Buat adopter baru
            new_adopter_id = uuid.uuid4()
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO sizopi.adopter
                    (id_adopter, username_adopter, total_kontribusi)
                    VALUES (%s, %s, %s)
                    RETURNING id_adopter
                """, [new_adopter_id, pengunjung['username_p'], 0])
                adopter_id = cursor.fetchone()[0]
        else:
            adopter_id = adopter_data[0]
        
        # Proses tipe adopter
        adopter_type = request.POST.get('adopter_type')
        
        if adopter_type == 'individu':
            # Get form values for individu
            nik = request.POST.get('nik')
            nama = request.POST.get('nama')
            no_telepon = request.POST.get('no_telepon', '')  # Default empty string
            
            # Cek apakah sudah ada data individu untuk adopter ini
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id_adopter, nik, nama
                    FROM sizopi.individu
                    WHERE id_adopter = %s
                """, [adopter_id])
                individu_data = cursor.fetchone()
            
            if individu_data:
                # Data individu sudah ada, update nama jika berbeda
                if individu_data[2] != nama:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE sizopi.individu
                            SET nama = %s
                            WHERE id_adopter = %s
                        """, [nama, adopter_id])
                
                # Gunakan NIK yang sudah ada (biarkan readonly di UI)
                nik = individu_data[1]
            else:
                # Belum ada data individu, cek apakah NIK sudah digunakan oleh adopter lain
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id_adopter, nama FROM sizopi.individu
                        WHERE nik = %s
                    """, [nik])
                    existing_nik = cursor.fetchone()
                
                if existing_nik and existing_nik[0] != adopter_id:
                    # NIK sudah digunakan adopter lain
                    messages.error(request, f"NIK {nik} sudah terdaftar atas nama {existing_nik[1]}")
                    return redirect('adopsi:admin_proses_adopsi', hewan_id=hewan_id)
                
                # Buat data individu baru
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO sizopi.individu
                        (id_adopter, nik, nama)
                        VALUES (%s, %s, %s)
                    """, [adopter_id, nik, nama])
            
            # FIXED: Update pengunjung data - CHECK IF COLUMN EXISTS
            alamat = request.POST.get('alamat', '')
            if alamat:
                try:
                    with connection.cursor() as cursor:
                        # Try to update alamat only first
                        cursor.execute("""
                            UPDATE sizopi.pengunjung
                            SET alamat = %s
                            WHERE username_p = %s
                        """, [alamat, pengunjung['username_p']])
                        
                        # Try to update no_telepon only if it exists
                        if no_telepon:
                            try:
                                cursor.execute("""
                                    UPDATE sizopi.pengunjung
                                    SET no_telepon = %s
                                    WHERE username_p = %s
                                """, [no_telepon, pengunjung['username_p']])
                            except Exception as tel_error:
                                # Column no_telepon doesn't exist in pengunjung table
                                print(f"no_telepon column doesn't exist in pengunjung: {tel_error}")
                                pass
                        
                except Exception as update_error:
                    print(f"Error updating pengunjung: {update_error}")
                    pass
            
            kontribusi = int(request.POST.get('kontribusi', 500000))
            periode = int(request.POST.get('periode', 3))
            status_pembayaran = request.POST.get('status_pembayaran', 'Tertunda')
            
        else:  # organisasi
            # Get form values for organisasi
            npp = request.POST.get('npp')
            nama_organisasi = request.POST.get('nama_organisasi')
            no_telepon_organisasi = request.POST.get('no_telepon_organisasi', '')
            
            # Cek apakah NPP sudah digunakan
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id_adopter, nama_organisasi 
                    FROM sizopi.organisasi
                    WHERE npp = %s
                """, [npp])
                existing_npp = cursor.fetchone()
            
            if existing_npp and existing_npp[0] != adopter_id:
                # NPP sudah digunakan oleh adopter lain
                messages.error(request, f"NPP {npp} sudah terdaftar untuk organisasi {existing_npp[1]}")
                return redirect('adopsi:admin_proses_adopsi', hewan_id=hewan_id)
            
            # Cek apakah sudah ada data organisasi
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id_adopter, npp, nama_organisasi
                    FROM sizopi.organisasi
                    WHERE id_adopter = %s AND npp = %s
                """, [adopter_id, npp])
                organisasi_data = cursor.fetchone()
            
            if organisasi_data:
                # Update data organisasi jika nama berbeda
                if organisasi_data[2] != nama_organisasi:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE sizopi.organisasi
                            SET nama_organisasi = %s
                            WHERE id_adopter = %s AND npp = %s
                        """, [nama_organisasi, adopter_id, npp])
            else:
                # Buat data organisasi baru
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO sizopi.organisasi
                        (id_adopter, npp, nama_organisasi)
                        VALUES (%s, %s, %s)
                    """, [adopter_id, npp, nama_organisasi])
            
            # FIXED: Update pengunjung data - safe version
            alamat_organisasi = request.POST.get('alamat_organisasi', '')
            if alamat_organisasi:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            UPDATE sizopi.pengunjung
                            SET alamat = %s
                            WHERE username_p = %s
                        """, [alamat_organisasi, pengunjung['username_p']])
                except Exception as update_error:
                    print(f"Error updating pengunjung alamat: {update_error}")
                    pass
            
            kontribusi = int(request.POST.get('kontribusi_organisasi', 500000))
            periode = int(request.POST.get('periode_organisasi', 3))
            status_pembayaran = request.POST.get('status_pembayaran_organisasi', 'Tertunda')
        
        # Simpan data adopsi
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sizopi.adopsi
                (id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial)
                VALUES (%s, %s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '%s months', %s)
                RETURNING id_adopter, id_hewan, tgl_mulai_adopsi, tgl_berhenti_adopsi
            """, [adopter_id, hewan_id, status_pembayaran, periode, kontribusi])
            adopsi_info = cursor.fetchone()
        
        # Update total kontribusi adopter jika status pembayaran adalah lunas
        if status_pembayaran == 'Lunas':
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sizopi.adopter
                    SET total_kontribusi = total_kontribusi + %s
                    WHERE id_adopter = %s
                """, [kontribusi, adopter_id])
        
        messages.success(request, f"Adopsi berhasil didaftarkan untuk {hewan['nama']}.")
        return redirect('adopsi:admin_detail_adopsi', 
                       id_adopter=adopsi_info[0], 
                       id_hewan=adopsi_info[1], 
                       tgl_mulai_adopsi=adopsi_info[2].strftime('%Y-%m-%d'))
    
    context = {
        'hewan': hewan,
    }
    return render(request, 'adopsi/admin/proses_adopsi.html', context)

def verify_username(request):
    """API untuk verifikasi username pengunjung"""
    username = request.GET.get('username', '')
    
    try:
        # Cek apakah pengguna ada di tabel pengunjung
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_p, alamat, tgl_lahir
                FROM sizopi.pengunjung
                WHERE username_p = %s
            """, [username])
            pengunjung_data = cursor.fetchone()
        
        if pengunjung_data:
            adopter_info = None
            
            # Ambil informasi pengguna untuk nama dan no telepon
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT username, email, nama_depan, nama_belakang, no_telepon
                    FROM sizopi.pengguna
                    WHERE username = %s
                """, [username])
                pengguna_data = cursor.fetchone()
            
            pengguna_info = {
                'username': pengguna_data[0],
                'email': pengguna_data[1],
                'nama_depan': pengguna_data[2],
                'nama_belakang': pengguna_data[3],
                'no_telepon': pengguna_data[4]
            } if pengguna_data else None
            
            # Cek apakah pengunjung sudah pernah menjadi adopter individu
            if pengguna_info:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT a.id_adopter, a.username_adopter, a.total_kontribusi
                        FROM sizopi.adopter a
                        JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
                        WHERE a.username_adopter = %s
                    """, [pengunjung_data[0]])
                    adopter_individu_data = cursor.fetchone()
                
                if adopter_individu_data:
                    adopter_id = adopter_individu_data[0]
                    
                    # Ambil data individu
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT id_adopter, nik, nama
                            FROM sizopi.individu
                            WHERE id_adopter = %s
                        """, [adopter_id])
                        individu_data = cursor.fetchone()
                    
                    if individu_data:
                        adopter_info = {
                            'type': 'individu',
                            'nik': individu_data[1],
                            'nama': individu_data[2]
                        }
            
            return JsonResponse({
                'exists': True,
                'pengunjung': {
                    'username_p': pengunjung_data[0],
                    'alamat': pengunjung_data[1],
                    'tgl_lahir': pengunjung_data[2].strftime('%Y-%m-%d') if pengunjung_data[2] else None
                },
                'pengguna': pengguna_info,
                'adopter': adopter_info
            })
        else:
            # Username tidak ditemukan
            return JsonResponse({
                'exists': False,
                'message': 'Username tidak ditemukan atau bukan role pengunjung'
            })
    except Exception as e:
        print(f"Error verifying username: {str(e)}")
        return JsonResponse({
            'exists': False,
            'error': str(e),
            'message': 'Terjadi kesalahan saat menghubungi server'
        }, status=500)

def laporan_kondisi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Menampilkan laporan kondisi hewan untuk adopter"""
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:dashboard_adopter')

    # Ambil data adopter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id_adopter, username_adopter, total_kontribusi
            FROM sizopi.adopter
            WHERE id_adopter = %s
        """, [id_adopter])
        adopter_data = cursor.fetchone()
    
    if not adopter_data:
        messages.error(request, "Data adopter tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    adopter = {
        'id_adopter': adopter_data[0],
        'username_adopter': adopter_data[1],
        'total_kontribusi': adopter_data[2]
    }
    
    # Ambil data hewan
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM sizopi.hewan
            WHERE id = %s
        """, [id_hewan])
        hewan_data = cursor.fetchone()
    
    if not hewan_data:
        messages.error(request, "Data hewan tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    hewan = {
        'id': hewan_data[0],
        'nama': hewan_data[1],
        'spesies': hewan_data[2],
        'asal_hewan': hewan_data[3],
        'tanggal_lahir': hewan_data[4],
        'status_kesehatan': hewan_data[5],
        'habitat': hewan_data[6],  # Ubah dari nama_habitat ke habitat
        'url_foto': hewan_data[7]
    }
    
    # Ambil data adopsi
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
            FROM sizopi.adopsi
            WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
            ORDER BY tgl_mulai_adopsi
        """, [id_adopter, id_hewan, tgl_mulai])
        adopsi_data = cursor.fetchone()
    
    if not adopsi_data:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:dashboard_adopter')
    
    # Bikin dummy object
    class AdopsiObject:
        pass
    
    adopsi = AdopsiObject()
    adopsi.status_pembayaran = adopsi_data[0]
    adopsi.tgl_mulai_adopsi = adopsi_data[1]
    adopsi.tgl_berhenti_adopsi = adopsi_data[2]
    adopsi.kontribusi_finansial = adopsi_data[3]
    
    # Medical records - tambahkan join dengan tabel dokter untuk nama_dokter
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT cm.id_hewan, cm.tanggal_pemeriksaan, cm.diagnosis, cm.pengobatan, 
                   cm.status_kesehatan, cm.catatan_tindak_lanjut, p.nama_depan AS nama_dokter
            FROM sizopi.catatan_medis cm
            LEFT JOIN sizopi.dokter_hewan d ON cm.username_dh = d.username_dh
            JOIN sizopi.pengguna p ON d.username_dh = p.username
            WHERE cm.id_hewan = %s AND cm.tanggal_pemeriksaan >= %s
            ORDER BY cm.tanggal_pemeriksaan DESC
        """, [id_hewan, tgl_mulai])
        medical_records_data = cursor.fetchall()
    
    # Convert to list of dictionaries
    medical_records = []
    for record in medical_records_data:
        medical_records.append({
            'id_hewan': record[0],
            'tanggal_pemeriksaan': record[1],
            'diagnosis': record[2],  # Konsisten dengan template
            'pengobatan': record[3],
            'status_kesehatan': record[4],
            'catatan_tindak_lanjut': record[5],
            'nama_dokter': record[6] if record[6] else 'Tidak diketahui'
        })
    
    context = {
        'adopsi': adopsi,
        'hewan': hewan,
        'adopter': adopter,
        'medical_records': medical_records,
        'now': timezone.now(),
        'tgl_mulai_adopsi_str': tgl_mulai.strftime('%Y-%m-%d'),
    }
    return render(request, 'adopsi/laporan_kondisi.html', context)

def sertifikat_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
   """Menampilkan sertifikat adopsi"""
   try:
       tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
   except ValueError:
       messages.error(request, "Format tanggal tidak valid.")
       return redirect('adopsi:dashboard_adopter')
   
   # Ambil data adopter
   with connection.cursor() as cursor:
       cursor.execute("""
           SELECT id_adopter, username_adopter, total_kontribusi
           FROM sizopi.adopter
           WHERE id_adopter = %s
       """, [id_adopter])
       adopter_data = cursor.fetchone()
   
   if not adopter_data:
       messages.error(request, "Data adopter tidak ditemukan.")
       return redirect('adopsi:dashboard_adopter')
   
   adopter = {
       'id_adopter': adopter_data[0],
       'username_adopter': adopter_data[1],
       'total_kontribusi': adopter_data[2]
   }
   
   # Ambil data hewan
   with connection.cursor() as cursor:
       cursor.execute("""
           SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
           FROM sizopi.hewan
           WHERE id = %s
       """, [id_hewan])
       hewan_data = cursor.fetchone()
   
   if not hewan_data:
       messages.error(request, "Data hewan tidak ditemukan.")
       return redirect('adopsi:dashboard_adopter')
   
   hewan = {
       'id': hewan_data[0],
       'nama': hewan_data[1],
       'spesies': hewan_data[2],
       'asal_hewan': hewan_data[3],
       'tanggal_lahir': hewan_data[4],
       'status_kesehatan': hewan_data[5],
       'nama_habitat': hewan_data[6],
       'url_foto': hewan_data[7]
   }
   
   # Ambil data adopsi
   with connection.cursor() as cursor:
       cursor.execute("""
           SELECT id_adopter, id_hewan, status_pembayaran, tgl_mulai_adopsi, tgl_berhenti_adopsi, kontribusi_finansial
           FROM sizopi.adopsi
           WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
           ORDER BY tgl_mulai_adopsi
       """, [id_adopter, id_hewan, tgl_mulai])
       adopsi_data = cursor.fetchone()
   
   if not adopsi_data:
       messages.error(request, "Data adopsi tidak ditemukan.")
       return redirect('adopsi:dashboard_adopter')
   
   # Buat manual dict
   adopsi = {
       'id_adopter__id_adopter': adopsi_data[0],
       'id_hewan__id': adopsi_data[1],
       'status_pembayaran': adopsi_data[2],
       'tgl_mulai_adopsi': adopsi_data[3],
       'tgl_mulai_adopsi_str': adopsi_data[3].strftime('%Y-%m-%d'),
       'tgl_berhenti_adopsi': adopsi_data[4],
       'tgl_berhenti_adopsi_str': adopsi_data[4].strftime('%Y-%m-%d'),
       'kontribusi_finansial': adopsi_data[5],
   }
   
   # Cek tipe adopter
   with connection.cursor() as cursor:
       cursor.execute("""
           SELECT id_adopter, nik, nama
           FROM sizopi.individu
           WHERE id_adopter = %s
       """, [id_adopter])
       individu_data = cursor.fetchone()
   
   if individu_data:
       adopter_type = 'individu'
       adopter_detail = {
           'id_adopter': individu_data[0],
           'nik': individu_data[1],
           'nama': individu_data[2]
       }
   else:
       with connection.cursor() as cursor:
           cursor.execute("""
               SELECT id_adopter, npp, nama_organisasi
               FROM sizopi.organisasi
               WHERE id_adopter = %s
           """, [id_adopter])
           organisasi_data = cursor.fetchone()
       
       if organisasi_data:
           adopter_type = 'organisasi'
           adopter_detail = {
               'id_adopter': organisasi_data[0],
               'npp': organisasi_data[1],
               'nama_organisasi': organisasi_data[2]
           }
       else:
           adopter_type = 'unknown'
           adopter_detail = None
   
   # Ambil data pengunjung
   with connection.cursor() as cursor:
       cursor.execute("""
           SELECT p.username_p, pe.username
           FROM sizopi.pengunjung p
           JOIN sizopi.pengguna pe ON p.username_p = pe.username
           JOIN sizopi.adopter a ON p.username_p = a.username_adopter
           WHERE a.id_adopter = %s
       """, [id_adopter])

def admin_hapus_adopsi(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    # FIXED: Check session authentication
    if 'username' not in request.session:
        messages.error(request, "Anda harus login untuk mengakses halaman admin.")
        return redirect('login')

    username = request.session['username']

    # Check admin using session username
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_sa FROM sizopi.staf_admin
                WHERE username_sa = %s
            """, [username])
            admin_data = cursor.fetchone()
        
        if not admin_data:
            messages.error(request, f"Username '{username}' tidak memiliki izin untuk menghapus adopsi.")
            return redirect('adopsi:admin_dashboard')
            
    except Exception as e:
        messages.error(request, f"Error verifying admin access: {str(e)}")
        return redirect('adopsi:admin_dashboard')
    
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:admin_dashboard')
    
    if request.method == 'POST':
        try:
            # Cek dulu apakah adopsi sudah berakhir
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT tgl_berhenti_adopsi FROM sizopi.adopsi
                    WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
                """, [id_adopter, id_hewan, tgl_mulai])
                adopsi_data = cursor.fetchone()
                
                if not adopsi_data:
                    messages.error(request, "Data adopsi tidak ditemukan.")
                    return redirect('adopsi:admin_detail_adopter', adopter_id=id_adopter)
                
                # Cek apakah adopsi sudah berakhir
                if adopsi_data[0] > timezone.now().date():
                    messages.error(request, "Tidak dapat menghapus adopsi yang masih aktif. Hentikan adopsi terlebih dahulu.")
                    return redirect('adopsi:admin_detail_adopter', adopter_id=id_adopter)
            
            # Hapus data adopsi
            with connection.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM sizopi.adopsi
                    WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
                """, [id_adopter, id_hewan, tgl_mulai])
                
                if cursor.rowcount > 0:
                    messages.success(request, "Data adopsi berhasil dihapus.")
                else:
                    messages.error(request, "Data adopsi tidak ditemukan.")
            
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat menghapus data adopsi: {str(e)}")
        
        return redirect('adopsi:admin_detail_adopter', adopter_id=id_adopter)
    
    # If not POST, redirect back
    return redirect('adopsi:admin_detail_adopter', adopter_id=id_adopter)

# FIX CURSOR ERROR di admin_dashboard

# RESTORE WORKING TRIGGER + FIX CURSOR

def admin_dashboard(request):
    """Dashboard - BACK TO WORKING VERSION with cursor fix"""
    
    # Session auth check
    if 'username' not in request.session:
        messages.error(request, "Anda harus login untuk mengakses halaman admin.")
        return redirect('login')
    
    username = request.session['username']
    
    # Check admin status
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_sa FROM sizopi.staf_admin
                WHERE username_sa = %s
            """, [username])
            admin_data = cursor.fetchone()
        
        if not admin_data:
            messages.error(request, f"Username '{username}' tidak memiliki akses admin.")
            # return redirect('dashboard:dashboard')
            
    except Exception as e:
        messages.error(request, f"Error verifying admin access: {str(e)}")
        # return redirect('dashboard:dashboard')
    
    # Statistics for the dashboard
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sizopi.hewan")
            total_animals = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sizopi.adopter")
            total_adopters = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM sizopi.adopsi
                WHERE tgl_berhenti_adopsi > CURRENT_DATE
            """)
            active_adoptions = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM sizopi.adopsi
                WHERE status_pembayaran = 'Tertunda'
            """)
            pending_payments = cursor.fetchone()[0]
    except Exception as e:
        messages.error(request, f"Error fetching statistics: {str(e)}")
        total_animals = total_adopters = active_adoptions = pending_payments = 0
    
    # BACK TO WORKING VERSION - Top adopters dengan kontribusi 1 tahun terakhir
    top_adopters = []
    try:
        # FIXED: Ambil data dalam satu query besar, tanpa nested cursor
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.id_adopter,
                    a.username_adopter,
                    -- Total kontribusi dari semua adopsi lunas (untuk display)
                    COALESCE(SUM(
                        CASE WHEN ad.status_pembayaran = 'Lunas' 
                             THEN ad.kontribusi_finansial 
                             ELSE 0 
                        END
                    ), 0) as total_kontribusi_lunas,
                    -- Kontribusi 1 tahun terakhir untuk ranking (INI YANG PENTING!)
                    COALESCE(SUM(
                        CASE 
                            WHEN ad.status_pembayaran = 'Lunas' 
                                 AND ad.tgl_mulai_adopsi >= CURRENT_DATE - INTERVAL '1 year'
                            THEN ad.kontribusi_finansial 
                            ELSE 0 
                        END
                    ), 0) as kontribusi_ranking,
                    -- Ambil nama dari JOIN
                    COALESCE(i.nama, o.nama_organisasi, 'Unknown') as nama_adopter,
                    CASE 
                        WHEN i.id_adopter IS NOT NULL THEN 'individu'
                        WHEN o.id_adopter IS NOT NULL THEN 'organisasi'
                        ELSE 'unknown'
                    END as adopter_type
                FROM sizopi.adopter a
                LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
                LEFT JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
                LEFT JOIN sizopi.organisasi o ON a.id_adopter = o.id_adopter
                GROUP BY a.id_adopter, a.username_adopter, i.nama, o.nama_organisasi, i.id_adopter, o.id_adopter
                -- RANKING berdasarkan kontribusi 1 tahun terakhir (TRIGGER SUKSES!)
                ORDER BY kontribusi_ranking DESC, total_kontribusi_lunas DESC
                LIMIT 5
            """)
            adopter_rows = cursor.fetchall()
            
            # Generate success message for top adopters (RESTORE INI!)
            if adopter_rows and adopter_rows[0][3] > 0:  # Ada kontribusi ranking
                top_adopter_name = adopter_rows[0][4]  # nama_adopter
                top_adopter_total = adopter_rows[0][2]  # total_kontribusi_lunas
                top_adopter_ranking = adopter_rows[0][3]  # kontribusi_ranking
                
                # TRIGGER SUKSES YANG HILANG! 🎯
                success_message = f"SUKSES: Daftar Top 5 Adopter satu tahun terakhir berhasil diperbarui, dengan peringkat pertama dengan nama adopter \"{top_adopter_name}\" berkontribusi sebesar \"Rp{top_adopter_ranking:,.0f}\" dalam 1 tahun terakhir (total kontribusi: Rp{top_adopter_total:,.0f})"
                messages.success(request, success_message)
        
        # Process each top adopter
        for adopter_row in adopter_rows:
            adopter_id = adopter_row[0]
            
            # Count adoptions dengan query terpisah
            with connection.cursor() as count_cursor:
                count_cursor.execute("""
                    SELECT COUNT(*) 
                    FROM sizopi.adopsi 
                    WHERE id_adopter = %s AND status_pembayaran = 'Lunas'
                """, [adopter_id])
                adopsi_count = count_cursor.fetchone()[0]
            
            adopter = {
                'id_adopter': adopter_id,
                'username_adopter': adopter_row[1],
                'total_kontribusi': adopter_row[2],        # Total semua kontribusi lunas
                'kontribusi_ranking': adopter_row[3],      # Kontribusi untuk ranking (1 tahun)
                'adopsi_count': adopsi_count,
                'nama': adopter_row[4],                    # nama_adopter dari JOIN
                'type': adopter_row[5]                     # adopter_type dari CASE
            }
            top_adopters.append(adopter)
                
    except Exception as e:
        print(f"DEBUG - Top adopters error: {str(e)}")
        messages.error(request, f"Error fetching top adopters: {str(e)}")
    
    # Get recent adoptions
    recent_adoptions = []
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    a.id_adopter, h.id, h.nama, a.status_pembayaran, 
                    a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial
                FROM sizopi.adopsi a
                JOIN sizopi.hewan h ON a.id_hewan = h.id
                ORDER BY a.tgl_mulai_adopsi DESC
                LIMIT 5
            """)
            adoption_rows = cursor.fetchall()
            
            for row in adoption_rows:
                adoption = {
                    'id_adopter': row[0],
                    'id_hewan': row[1],
                    'hewan_nama': row[2],
                    'status_pembayaran': row[3],
                    'tgl_mulai_adopsi': row[4],
                    'tgl_berhenti_adopsi': row[5],
                    'kontribusi_finansial': row[6]
                }
                recent_adoptions.append(adoption)
                
    except Exception as e:
        print(f"DEBUG - Recent adoptions error: {str(e)}")
        messages.error(request, f"Error fetching recent adoptions: {str(e)}")
    
    context = {
        'total_animals': total_animals,
        'total_adopters': total_adopters,
        'active_adoptions': active_adoptions,
        'pending_payments': pending_payments,
        'top_adopters': top_adopters,
        'recent_adoptions': recent_adoptions,
        'now': timezone.now(),
    }
    return render(request, 'adopsi/admin_dashboard.html', context)

def admin_daftar_adopter(request):
    """Menampilkan daftar adopter untuk admin - FIXED for session auth"""
    
    # FIXED: Check session authentication
    if 'username' not in request.session:
        messages.error(request, "Anda harus login untuk mengakses halaman admin.")
        return redirect('login')
    
    username = request.session['username']
    
    # Check admin status using session username
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_sa FROM sizopi.staf_admin 
                WHERE username_sa = %s
            """, [username])
            admin_data = cursor.fetchone()
            
        if not admin_data:
            messages.error(request, f"Username '{username}' tidak memiliki akses admin untuk melihat daftar adopter.")
            # return redirect('main:home')
            
    except Exception as e:
        messages.error(request, f"Error verifying admin access: {str(e)}")
        # return redirect('main:home')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '').strip()
    adopter_type = request.GET.get('type', 'all')
    
    # Build base queries based on adopter type
    if adopter_type == 'individu':
        base_query = """
            SELECT DISTINCT
                a.id_adopter, 
                a.username_adopter, 
                COALESCE(SUM(CASE WHEN ad.status_pembayaran = 'Lunas' THEN ad.kontribusi_finansial ELSE 0 END), 0) as total_kontribusi,
                i.nama as nama_adopter,
                'individu' as type,
                i.nik as identifier
            FROM sizopi.adopter a
            INNER JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
            LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
        """
        count_base = """
            SELECT COUNT(DISTINCT a.id_adopter) 
            FROM sizopi.adopter a
            INNER JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
        """
        group_by = " GROUP BY a.id_adopter, a.username_adopter, i.nama, i.nik"
        
    elif adopter_type == 'organisasi':
        base_query = """
            SELECT DISTINCT
                a.id_adopter, 
                a.username_adopter, 
                COALESCE(SUM(CASE WHEN ad.status_pembayaran = 'Lunas' THEN ad.kontribusi_finansial ELSE 0 END), 0) as total_kontribusi,
                o.nama_organisasi as nama_adopter,
                'organisasi' as type,
                o.npp as identifier
            FROM sizopi.adopter a
            INNER JOIN sizopi.organisasi o ON a.id_adopter = o.id_adopter
            LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
        """
        count_base = """
            SELECT COUNT(DISTINCT a.id_adopter) 
            FROM sizopi.adopter a
            INNER JOIN sizopi.organisasi o ON a.id_adopter = o.id_adopter
        """
        group_by = " GROUP BY a.id_adopter, a.username_adopter, o.nama_organisasi, o.npp"
        
    else:  # all
        base_query = """
            SELECT DISTINCT
                a.id_adopter, 
                a.username_adopter, 
                COALESCE(SUM(CASE WHEN ad.status_pembayaran = 'Lunas' THEN ad.kontribusi_finansial ELSE 0 END), 0) as total_kontribusi,
                COALESCE(i.nama, o.nama_organisasi) as nama_adopter,
                CASE 
                    WHEN i.id_adopter IS NOT NULL THEN 'individu'
                    WHEN o.id_adopter IS NOT NULL THEN 'organisasi'
                    ELSE 'unknown'
                END as type,
                COALESCE(i.nik, o.npp) as identifier
            FROM sizopi.adopter a
            LEFT JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
            LEFT JOIN sizopi.organisasi o ON a.id_adopter = o.id_adopter
            LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter
        """
        count_base = """
            SELECT COUNT(DISTINCT a.id_adopter) 
            FROM sizopi.adopter a
            LEFT JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
            LEFT JOIN sizopi.organisasi o ON a.id_adopter = o.id_adopter
        """
        group_by = " GROUP BY a.id_adopter, a.username_adopter, i.nama, o.nama_organisasi, i.nik, o.npp"
    
    # Build WHERE conditions for search
    where_conditions = []
    count_where_conditions = []
    params = []
    count_params = []
    
    if search_query:
        if adopter_type == 'individu':
            where_conditions.append("i.nama ILIKE %s")
            count_where_conditions.append("i.nama ILIKE %s")
            params.append(f"%{search_query}%")
            count_params.append(f"%{search_query}%")
        elif adopter_type == 'organisasi':
            where_conditions.append("o.nama_organisasi ILIKE %s")
            count_where_conditions.append("o.nama_organisasi ILIKE %s")
            params.append(f"%{search_query}%")
            count_params.append(f"%{search_query}%")
        else:  # all
            where_conditions.append("(i.nama ILIKE %s OR o.nama_organisasi ILIKE %s)")
            count_where_conditions.append("(i.nama ILIKE %s OR o.nama_organisasi ILIKE %s)")
            params.extend([f"%{search_query}%", f"%{search_query}%"])
            count_params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    # Finalize queries
    if where_conditions:
        base_query += " WHERE " + " AND ".join(where_conditions)
    
    if count_where_conditions:
        count_query = count_base + " WHERE " + " AND ".join(count_where_conditions)
    else:
        count_query = count_base
    
    base_query += group_by + " ORDER BY total_kontribusi DESC"
    
    # Get total count for pagination
    try:
        with connection.cursor() as cursor:
            cursor.execute(count_query, count_params)
            total_items = cursor.fetchone()[0]
    except Exception as e:
        messages.error(request, f"Error counting adopters: {str(e)}")
        total_items = 0
    
    # Pagination setup
    items_per_page = 15
    try:
        page_number = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_number = 1
    
    if page_number < 1:
        page_number = 1
    
    offset = (page_number - 1) * items_per_page
    
    # Add pagination to main query
    final_query = base_query + " LIMIT %s OFFSET %s"
    final_params = params + [items_per_page, offset]
    
    # Execute main query and process results
    adopters = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(final_query, final_params)
            adopters_data = cursor.fetchall()
        
        # Process each adopter
        for row in adopters_data:
            adopter = {
                'id_adopter': row[0],
                'username_adopter': row[1],
                'total_kontribusi': row[2],
                'nama': row[3] or 'Unknown',
                'type': row[4],
                'identifier': row[5] or '-',
                'is_active': False  # Will be determined below
            }
            
            # Check if adopter is currently active (has ongoing adoptions)
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM sizopi.adopsi 
                        WHERE id_adopter = %s AND tgl_berhenti_adopsi > CURRENT_DATE
                    """, [adopter['id_adopter']])
                    active_count = cursor.fetchone()[0]
                    adopter['is_active'] = active_count > 0
            except Exception as e:
                # If there's an error checking active status, assume not active
                adopter['is_active'] = False
            
            adopters.append(adopter)
            
    except Exception as e:
        messages.error(request, f"Error fetching adopters: {str(e)}")
        adopters = []
    
    # Create pagination object
    total_pages = (total_items + items_per_page - 1) // items_per_page if total_items > 0 else 1
    has_previous = page_number > 1
    has_next = page_number < total_pages
    
    # Limit page range for better UI (show max 5 pages around current)
    page_range_start = max(1, page_number - 2)
    page_range_end = min(total_pages + 1, page_number + 3)
    
    # Create paginator-like object for template compatibility
    page_obj = {
        'object_list': adopters,
        'number': page_number,
        'has_previous': has_previous,
        'has_next': has_next,
        'previous_page_number': page_number - 1 if has_previous else None,
        'next_page_number': page_number + 1 if has_next else None,
        'paginator': {
            'num_pages': total_pages,
            'count': total_items,
            'page_range': range(page_range_start, page_range_end)
        }
    }
    
    # Prepare context for template
    context = {
        'adopters': page_obj,
        'search_query': search_query,
        'adopter_type': adopter_type,
    }
    
    return render(request, 'adopsi/admin/daftar_adopter.html', context)

def admin_hapus_adopter(request, adopter_id, adopter_type):
    """FIXED: Hapus adopter - using session auth"""
    
    # FIXED: Check session authentication
    if 'username' not in request.session:
        messages.error(request, "Anda harus login untuk mengakses halaman admin.")
        return redirect('login')
    
    username = request.session['username']
    
    # Check admin status
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT username_sa FROM sizopi.staf_admin
                WHERE username_sa = %s
            """, [username])
            admin_data = cursor.fetchone()
        
        if not admin_data:
            messages.error(request, f"Username '{username}' tidak memiliki akses admin untuk menghapus adopter.")
            return redirect('adopsi:admin_daftar_adopter')
            
    except Exception as e:
        messages.error(request, f"Error verifying admin access: {str(e)}")
        return redirect('adopsi:admin_daftar_adopter')
    
    # Validasi adopter_type
    if adopter_type not in ['individu', 'organisasi']:
        messages.error(request, "Tipe adopter tidak valid.")
        return redirect('adopsi:admin_daftar_adopter')
    
    try:
        # Cek apakah adopter sedang aktif berdasarkan type
        if adopter_type == 'individu':
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM sizopi.adopsi a
                    JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
                    WHERE i.id_adopter = %s AND a.tgl_berhenti_adopsi > CURRENT_DATE
                """, [adopter_id])
                active_count = cursor.fetchone()[0]
                
                if active_count > 0:
                    messages.error(request, "Tidak dapat menghapus adopter individu yang masih aktif mengadopsi satwa.")
                    return redirect('adopsi:admin_daftar_adopter')
                
                # Hapus data adopsi untuk individu ini
                cursor.execute("""
                    DELETE FROM sizopi.adopsi 
                    WHERE id_adopter IN (
                        SELECT id_adopter FROM sizopi.individu WHERE id_adopter = %s
                    )
                """, [adopter_id])
                
                # Hapus data individu
                cursor.execute("""
                    DELETE FROM sizopi.individu WHERE id_adopter = %s
                """, [adopter_id])
                
                messages.success(request, "Data adopter individu dan riwayat adopsinya berhasil dihapus.")
                
        elif adopter_type == 'organisasi':
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM sizopi.adopsi a
                    JOIN sizopi.organisasi o ON a.id_adopter = o.id_adopter
                    WHERE o.id_adopter = %s AND a.tgl_berhenti_adopsi > CURRENT_DATE
                """, [adopter_id])
                active_count = cursor.fetchone()[0]
                
                if active_count > 0:
                    messages.error(request, "Tidak dapat menghapus adopter organisasi yang masih aktif mengadopsi satwa.")
                    return redirect('adopsi:admin_daftar_adopter')
                
                # Hapus data adopsi untuk organisasi ini
                cursor.execute("""
                    DELETE FROM sizopi.adopsi 
                    WHERE id_adopter IN (
                        SELECT id_adopter FROM sizopi.organisasi WHERE id_adopter = %s
                    )
                """, [adopter_id])
                
                # Hapus data organisasi
                cursor.execute("""
                    DELETE FROM sizopi.organisasi WHERE id_adopter = %s
                """, [adopter_id])
                
                messages.success(request, "Data adopter organisasi dan riwayat adopsinya berhasil dihapus.")
        
        # Cek apakah masih ada data individu/organisasi lain untuk adopter ini
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM sizopi.individu WHERE id_adopter = %s) as individu_count,
                    (SELECT COUNT(*) FROM sizopi.organisasi WHERE id_adopter = %s) as organisasi_count
            """, [adopter_id, adopter_id])
            counts = cursor.fetchone()
            
            # Jika tidak ada data individu atau organisasi lagi, hapus adopter
            if counts[0] == 0 and counts[1] == 0:
                cursor.execute("""
                    DELETE FROM sizopi.adopter WHERE id_adopter = %s
                """, [adopter_id])
                messages.info(request, "Data adopter utama juga dihapus karena tidak ada data individu/organisasi yang tersisa.")
        
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus data adopter: {str(e)}")
    
    return redirect('adopsi:admin_daftar_adopter')

def admin_detail_adopter(request, adopter_id, adopter_type=None):
    """Detail adopter BERDASARKAN TYPE dengan total kontribusi yang benar - FINAL VERSION"""
    # Cek apakah user adalah admin
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sizopi.staf_admin 
            WHERE username_sa = %s
        """, [request.user.username])
        is_admin = cursor.fetchone() is not None
    
    # FIXED: Ambil data adopter dengan total kontribusi yang dihitung ulang dari adopsi lunas
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.id_adopter, 
                a.username_adopter, 
                -- Hitung ulang total kontribusi dari adopsi lunas
                COALESCE(SUM(ad.kontribusi_finansial), 0) as total_kontribusi_lunas
            FROM sizopi.adopter a
            LEFT JOIN sizopi.adopsi ad ON a.id_adopter = ad.id_adopter AND ad.status_pembayaran = 'Lunas'
            WHERE a.id_adopter = %s
            GROUP BY a.id_adopter, a.username_adopter
        """, [adopter_id])
        adopter_data = cursor.fetchone()
    
    if not adopter_data:
        messages.error(request, "Data adopter tidak ditemukan.")
        return redirect('adopsi:admin_daftar_adopter')
    
    adopter = {
        'id_adopter': adopter_data[0],
        'username_adopter': adopter_data[1],
        'total_kontribusi': adopter_data[2]  # Total kontribusi lunas yang benar
    }
    
    # DETERMINE TYPE jika tidak ada parameter
    if not adopter_type:
        # Cek dulu individu
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter FROM sizopi.individu
                WHERE id_adopter = %s
            """, [adopter_id])
            if cursor.fetchone():
                adopter_type = 'individu'
            else:
                # Cek organisasi
                cursor.execute("""
                    SELECT id_adopter FROM sizopi.organisasi
                    WHERE id_adopter = %s
                """, [adopter_id])
                if cursor.fetchone():
                    adopter_type = 'organisasi'
                else:
                    adopter_type = 'unknown'
    
    # Ambil detail berdasarkan type
    adopter_detail = None
    if adopter_type == 'individu':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter, nik, nama
                FROM sizopi.individu
                WHERE id_adopter = %s
            """, [adopter_id])
            individu_data = cursor.fetchone()
        
        if individu_data:
            adopter_detail = {
                'id_adopter': individu_data[0],
                'nik': individu_data[1],
                'nama': individu_data[2]
            }
    
    elif adopter_type == 'organisasi':
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id_adopter, npp, nama_organisasi
                FROM sizopi.organisasi
                WHERE id_adopter = %s
            """, [adopter_id])
            organisasi_data = cursor.fetchone()
        
        if organisasi_data:
            adopter_detail = {
                'id_adopter': organisasi_data[0],
                'npp': organisasi_data[1],
                'nama_organisasi': organisasi_data[2]
            }
    
    # Ambil data pengunjung
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.username_p, p.alamat, p.tgl_lahir, pe.email, 
                   pe.nama_depan, pe.nama_belakang
            FROM sizopi.pengunjung p
            JOIN sizopi.pengguna pe ON p.username_p = pe.username
            JOIN sizopi.adopter a ON p.username_p = a.username_adopter
            WHERE a.id_adopter = %s
        """, [adopter_id])
        pengunjung_data = cursor.fetchone()
    
    pengunjung = None
    if pengunjung_data:
        pengunjung = {
            'username_p': pengunjung_data[0],
            'alamat': pengunjung_data[1],
            'tgl_lahir': pengunjung_data[2],
            'email': pengunjung_data[3],
            'nama_lengkap': f"{pengunjung_data[4]} {pengunjung_data[5]}" if pengunjung_data[4] and pengunjung_data[5] else pengunjung_data[4] or pengunjung_data[5] or ""
        }
    
    # Ambil data adopsi BERDASARKAN TYPE - HANYA YANG STATUS LUNAS
    if adopter_type == 'individu':
        adoption_query = """
            SELECT a.id_adopter, h.id, h.nama, h.spesies, h.url_foto,
                   a.status_pembayaran, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial
            FROM sizopi.adopsi a
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            JOIN sizopi.individu i ON a.id_adopter = i.id_adopter
            WHERE i.id_adopter = %s AND a.status_pembayaran = 'Lunas'
            ORDER BY a.tgl_mulai_adopsi DESC
        """
    elif adopter_type == 'organisasi':
        adoption_query = """
            SELECT a.id_adopter, h.id, h.nama, h.spesies, h.url_foto,
                   a.status_pembayaran, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial
            FROM sizopi.adopsi a
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            JOIN sizopi.organisasi o ON a.id_adopter = o.id_adopter
            WHERE o.id_adopter = %s AND a.status_pembayaran = 'Lunas'
            ORDER BY a.tgl_mulai_adopsi DESC
        """
    else:
        adoption_query = """
            SELECT a.id_adopter, h.id, h.nama, h.spesies, h.url_foto,
                   a.status_pembayaran, a.tgl_mulai_adopsi, a.tgl_berhenti_adopsi, a.kontribusi_finansial
            FROM sizopi.adopsi a
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            WHERE a.id_adopter = %s AND a.status_pembayaran = 'Lunas'
            ORDER BY a.tgl_mulai_adopsi DESC
        """
    
    with connection.cursor() as cursor:
        cursor.execute(adoption_query, [adopter_id])
        adoptions_data = cursor.fetchall()
    
    # Process adoptions data
    adoptions = []
    for adoption_row in adoptions_data:
        adoption = {
            'id_adopter__id_adopter': adoption_row[0],
            'id_hewan__id': adoption_row[1],
            'id_hewan__nama': adoption_row[2],
            'id_hewan__spesies': adoption_row[3],
            'id_hewan__url_foto': adoption_row[4],
            'status_pembayaran': adoption_row[5],
            'tgl_mulai_adopsi': adoption_row[6],
            'tgl_mulai_adopsi_str': adoption_row[6].strftime('%Y-%m-%d'),
            'tgl_berhenti_adopsi': adoption_row[7],
            'kontribusi_finansial': adoption_row[8]
        }
        adoptions.append(adoption)
    
    context = {
        'adopter': adopter,
        'adopter_type': adopter_type,
        'adopter_detail': adopter_detail,
        'pengunjung': pengunjung,
        'adoptions': adoptions,
        'now': timezone.now(),
    }
    return render(request, 'adopsi/admin/detail_adopter.html', context)

def admin_update_payment(request, id_adopter, id_hewan, tgl_mulai_adopsi):
    """Update status pembayaran adopsi oleh admin - FINAL VERSION dengan auto update total kontribusi"""
    
    # Cek apakah user adalah admin
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM sizopi.staf_admin 
            WHERE username_sa = %s
        """, [request.user.username])
        is_admin = cursor.fetchone() is not None
    
    try:
        tgl_mulai = datetime.strptime(tgl_mulai_adopsi, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, "Format tanggal tidak valid.")
        return redirect('adopsi:admin_dashboard')

    if request.method == 'POST':
        new_status = request.POST.get('status_pembayaran', '').strip()
        
        # Validasi input
        if new_status.lower() in ['tertunda', 'lunas']:
            # Normalize ke format yang benar
            normalized_status = new_status.capitalize()  # 'Tertunda' atau 'Lunas'
            
            try:
                # Update status pembayaran dengan SQL
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE sizopi.adopsi 
                        SET status_pembayaran = %s
                        WHERE id_adopter = %s AND id_hewan = %s AND tgl_mulai_adopsi = %s
                    """, [normalized_status, id_adopter, id_hewan, tgl_mulai])
                    
                    if cursor.rowcount > 0:
                        # FIXED: Update total kontribusi adopter setelah mengubah status
                        cursor.execute("""
                            UPDATE sizopi.adopter 
                            SET total_kontribusi = (
                                SELECT COALESCE(SUM(kontribusi_finansial), 0)
                                FROM sizopi.adopsi 
                                WHERE sizopi.adopsi.id_adopter = sizopi.adopter.id_adopter 
                                AND status_pembayaran = 'Lunas'
                            )
                            WHERE id_adopter = %s
                        """, [id_adopter])
                        
                        messages.success(request, f"Status pembayaran berhasil diubah menjadi '{normalized_status}' dan total kontribusi telah diperbarui.")
                    else:
                        messages.error(request, "Data adopsi tidak ditemukan atau tidak ada perubahan.")
                        
            except Exception as e:
                messages.error(request, f"Gagal mengupdate status pembayaran: {str(e)}")
        else:
            messages.error(request, f"Status pembayaran tidak valid: '{new_status}'. Harus 'Tertunda' atau 'Lunas'.")
            
        return redirect('adopsi:admin_detail_adopsi', 
                       id_adopter=id_adopter, 
                       id_hewan=id_hewan, 
                       tgl_mulai_adopsi=tgl_mulai_adopsi)

    # GET request - tampilkan form
    # Ambil data adopsi lengkap dengan join
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                a.status_pembayaran, 
                a.tgl_mulai_adopsi, 
                a.tgl_berhenti_adopsi, 
                a.kontribusi_finansial,
                ad.id_adopter,
                ad.username_adopter,
                h.id as hewan_id,
                h.nama as hewan_nama,
                h.spesies,
                h.url_foto
            FROM sizopi.adopsi a
            JOIN sizopi.adopter ad ON a.id_adopter = ad.id_adopter
            JOIN sizopi.hewan h ON a.id_hewan = h.id
            WHERE ad.id_adopter = %s AND a.id_hewan = %s AND a.tgl_mulai_adopsi = %s
        """, [id_adopter, id_hewan, tgl_mulai])
        
        data = cursor.fetchone()
    
    if not data:
        messages.error(request, "Data adopsi tidak ditemukan.")
        return redirect('adopsi:admin_dashboard')
    
    # Buat context sederhana dengan dict biasa
    context = {
        'adopsi': {
            'status_pembayaran': data[0],
            'tgl_mulai_adopsi': data[1],
            'tgl_berhenti_adopsi': data[2],
            'kontribusi_finansial': data[3],
        },
        'adopter': {
            'id_adopter': data[4],
            'username_adopter': data[5],
        },
        'hewan': {
            'id': data[6],
            'nama': data[7],
            'spesies': data[8],
            'url_foto': data[9],
        },
        'tgl_mulai_adopsi_str': tgl_mulai_adopsi,
    }