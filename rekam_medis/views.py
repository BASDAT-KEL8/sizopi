from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages

import psycopg2

def get_db_connection():
    return psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        sslmode='require',
        options='-c search_path=sizopi'
    )

def is_dokter_hewan(request):
    username = request.session.get('username')
    if not username:
        return False
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dokter_hewan WHERE username_dh = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return bool(result)

def list_rekam_medis(request):
    if not is_dokter_hewan(request):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    conn = get_db_connection()
    cur = conn.cursor()
    # Ambil semua hewan
    cur.execute("SELECT id, nama, spesies FROM hewan ORDER BY nama")
    hewan_rows = cur.fetchall()
    daftar_hewan = []
    for h in hewan_rows:
        hewan_id, nama, spesies = h
        # Ambil rekam medis untuk hewan ini
        cur.execute("""
            SELECT id_hewan, tanggal_pemeriksaan, username_dh, status_kesehatan, diagnosis, pengobatan, catatan_tindak_lanjut
            FROM catatan_medis
            WHERE id_hewan = %s
            ORDER BY tanggal_pemeriksaan DESC
        """, (hewan_id,))
        rekam_medis = [
            {
                'id_hewan': row[0],
                'tanggal_pemeriksaan': row[1],
                'nama_dokter': row[2],
                'status_kesehatan': row[3],
                'diagnosis': row[4],
                'pengobatan': row[5],
                'catatan_tindak_lanjut': row[6],
            }
            for row in cur.fetchall()
        ]
        daftar_hewan.append({
            'id': hewan_id,
            'nama': nama,
            'spesies': spesies,
            'rekam_medis': rekam_medis
        })
    cur.close()
    conn.close()
    return render(request, 'rekam_medis/rekam_medis_list.html', {'daftar_hewan': daftar_hewan})

# @login_required
def tambah_rekam_medis(request):
    if not is_dokter_hewan(request):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    id_hewan = request.GET.get('id_hewan') or request.POST.get('id_hewan')
    hewan_nama = hewan_spesies = None
    context = {}
    username = request.session.get('username')
    if not username:
        return redirect('login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT nama_depan, nama_tengah, nama_belakang, username, email, no_telepon
        FROM pengguna WHERE username = %s
    """, (username,))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return redirect('login')
    nama_depan, nama_tengah, nama_belakang, username, email, no_telepon = user
    context['nama_lengkap'] = f"{nama_depan} {nama_tengah or ''} {nama_belakang}".strip()
    context['username'] = username
    context['email'] = email
    context['no_telepon'] = no_telepon
    cur.close()
    conn.close()

    if id_hewan:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT nama, spesies FROM hewan WHERE id = %s", (id_hewan,))
        row = cur.fetchone()
        if row:
            hewan_nama, hewan_spesies = row
        cur.close()
        conn.close()
    
    if request.method == 'POST':
        tanggal_pemeriksaan = request.POST.get('tanggal_pemeriksaan')
        status_kesehatan = request.POST.get('status_kesehatan')
        diagnosis = request.POST.get('diagnosis')
        pengobatan = request.POST.get('pengobatan')
        catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT username_dh FROM dokter_hewan WHERE username_dh = %s", (username,))
        dokter_row = cur.fetchone()
        if not dokter_row:
            cur.close()
            conn.close()
            return render(request, 'rekam_medis/rekam_medis_form.html', {
                'error': 'Akun Anda tidak terdaftar sebagai dokter hewan.',
                'id_hewan': id_hewan, 'hewan_nama': hewan_nama, 'hewan_spesies': hewan_spesies
            })
        username_dh = dokter_row[0]
        
        if not (id_hewan and tanggal_pemeriksaan and status_kesehatan):
            cur.close()
            conn.close()
            return render(request, 'rekam_medis/rekam_medis_form.html', {
                'error': 'ID Hewan, Tanggal Pemeriksaan, dan Status Kesehatan wajib diisi.',
                'id_hewan': id_hewan, 'hewan_nama': hewan_nama, 'hewan_spesies': hewan_spesies
            })
        
        try:
            cur.execute("""
                INSERT INTO catatan_medis (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id_hewan, username_dh, tanggal_pemeriksaan, diagnosis, pengobatan, status_kesehatan, catatan_tindak_lanjut))
            # Update status_kesehatan di tabel hewan
            cur.execute("UPDATE hewan SET status_kesehatan = %s WHERE id = %s", (status_kesehatan, id_hewan))
            conn.commit()
            # Ambil pesan NOTICE dari trigger jika ada
            if hasattr(cur.connection, 'notices') and cur.connection.notices:
                for notice in cur.connection.notices:
                    messages.info(request, notice)
                cur.connection.notices.clear()
            if status_kesehatan == 'Sakit':
                cur.execute("SELECT nama FROM hewan WHERE id = %s", (id_hewan,))
                hewan_nama = cur.fetchone()[0]
                messages.success(request, f'SUKSES: Jadwal pemeriksaan hewan "{hewan_nama}" telah diperbarui karena status kesehatan "Sakit".')
            else:
                messages.success(request, 'Rekam medis berhasil ditambahkan.')
            
            cur.close()
            conn.close()
            return redirect('rekam_medis:list_rekam_medis')
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return render(request, 'rekam_medis/rekam_medis_form.html', {
                'error': f'Gagal menyimpan: {str(e)}',
                'id_hewan': id_hewan, 'hewan_nama': hewan_nama, 'hewan_spesies': hewan_spesies
            })
    else:
        return render(request, 'rekam_medis/rekam_medis_form.html', {'id_hewan': id_hewan, 'hewan_nama': hewan_nama, 'hewan_spesies': hewan_spesies})

def hapus_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
    if not is_dokter_hewan(request):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM catatan_medis WHERE id_hewan = %s AND tanggal_pemeriksaan = %s", (id_hewan, tanggal_pemeriksaan))
            conn.commit()
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            return render(request, 'rekam_medis/rekam_medis_confirm_delete.html', {
                'id_hewan': id_hewan,
                'tanggal_pemeriksaan': tanggal_pemeriksaan,
                'error': f'Gagal menghapus: {str(e)}'
            })
        cur.close()
        conn.close()
        return redirect('rekam_medis:list_rekam_medis')
    # INI buat nampilin halaman konfirmasi
    return render(request, 'rekam_medis/rekam_medis_confirm_delete.html', {
        'id_hewan': id_hewan,
        'tanggal_pemeriksaan': tanggal_pemeriksaan
    })

def edit_rekam_medis(request, id_hewan, tanggal_pemeriksaan):
    if not is_dokter_hewan(request):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT diagnosis, pengobatan, catatan_tindak_lanjut
        FROM catatan_medis
        WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
    """, (id_hewan, tanggal_pemeriksaan))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        messages.error(request, 'Data rekam medis tidak ditemukan.')
        return redirect('rekam_medis:list_rekam_medis')

    if request.method == 'POST':
        diagnosis = request.POST.get('diagnosis', '')
        pengobatan = request.POST.get('pengobatan', '')
        catatan_tindak_lanjut = request.POST.get('catatan_tindak_lanjut', '')

        try:
            cur.execute("""
                UPDATE catatan_medis
                SET diagnosis = %s, pengobatan = %s, catatan_tindak_lanjut = %s
                WHERE id_hewan = %s AND tanggal_pemeriksaan = %s
            """, (diagnosis, pengobatan, catatan_tindak_lanjut, id_hewan, tanggal_pemeriksaan))
            conn.commit()
            messages.success(request, 'Rekam medis berhasil diperbarui.')
            cur.close()
            conn.close()
            return redirect('rekam_medis:list_rekam_medis')
        except Exception as e:
            conn.rollback()
            messages.error(request, f'Gagal memperbarui: {str(e)}')

    context = {
        'diagnosis': row[0] or '',
        'pengobatan': row[1] or '',
        'catatan_tindak_lanjut': row[2] or '',
    }
    cur.close()
    conn.close()
    return render(request, 'rekam_medis/rekam_medis_edit.html', context)