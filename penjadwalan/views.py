from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

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

def check_dokter_hewan(view_func):
    def wrapper(request, *args, **kwargs):
        if not is_dokter_hewan(request):
            messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@check_dokter_hewan
def list_jadwal_pemeriksaan(request):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ambil semua hewan
    cur.execute("SELECT id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan FROM hewan ORDER BY nama")
    hewan_rows = cur.fetchall()
    hewan_list = []
    
    for h in hewan_rows:
        # Ambil frekuensi pemeriksaan untuk hewan ini
        cur.execute("SELECT freq_pemeriksaan_rutin FROM jadwal_pemeriksaan_kesehatan WHERE id_hewan = %s LIMIT 1", (h[0],))
        freq_row = cur.fetchone()
        freq_pemeriksaan = freq_row[0] if freq_row else None
        
        hewan_list.append({
            'id': h[0],
            'nama': h[1],
            'spesies': h[2],
            'asal_hewan': h[3],
            'tanggal_lahir': h[4],
            'habitat': h[5],
            'status_kesehatan': h[6],
            'freq_pemeriksaan_rutin': freq_pemeriksaan,  # Tambahkan ini
        })
    
    # Ambil semua jadwal
    cur.execute("SELECT id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin FROM jadwal_pemeriksaan_kesehatan ORDER BY tgl_pemeriksaan_selanjutnya")
    jadwal_rows = cur.fetchall()
    jadwal_list = []
    for j in jadwal_rows:
        jadwal_list.append({
            'id_hewan': j[0],
            'tgl_pemeriksaan_selanjutnya': j[1],
            'freq_pemeriksaan_rutin': j[2],
            'id': f"{j[0]}_{j[1]}"
        })
    
    cur.close()
    conn.close()
    
    context = {
        'hewan_list': hewan_list,
        'jadwal_list': jadwal_list,
        'show_freq': True
    }
    return render(request, 'penjadwalan/list_jadwal_pemeriksaan.html', context)

@check_dokter_hewan
def tambah_jadwal_pemeriksaan(request, id_hewan):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan FROM hewan WHERE id = %s", (id_hewan,))
    row = cur.fetchone()
    hewan = None
    if row:
        hewan = {
            'id': row[0],
            'nama': row[1],
            'spesies': row[2],
            'asal_hewan': row[3],
            'tanggal_lahir': row[4],
            'habitat': row[5],
            'status_kesehatan': row[6],
        }
    if request.method == 'POST':
        tgl_pemeriksaan = request.POST.get('tgl_pemeriksaan')
        cur.execute("SELECT freq_pemeriksaan_rutin FROM jadwal_pemeriksaan_kesehatan WHERE id_hewan = %s ORDER BY tgl_pemeriksaan_selanjutnya DESC LIMIT 1", (id_hewan,))
        freq_row = cur.fetchone()
        freq = freq_row[0] if freq_row else 3
        try:
            cur.execute("INSERT INTO jadwal_pemeriksaan_kesehatan (id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin) VALUES (%s, %s, %s)", (id_hewan, tgl_pemeriksaan, freq))
            conn.commit()
            cur.execute("SELECT nama FROM hewan WHERE id = %s", (id_hewan,))
            hewan_nama = cur.fetchone()[0]
            messages.success(request, f'SUKSES: Jadwal pemeriksaan rutin hewan "{hewan_nama}" telah ditambahkan sesuai frekuensi.')
            cur.close()
            conn.close()
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            messages.error(request, f'Gagal menambah jadwal: {str(e)}')
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
    cur.close()
    conn.close()
    return render(request, 'penjadwalan/tambah_jadwal.html', {'hewan': hewan})

@check_dokter_hewan
def edit_jadwal_pemeriksaan(request, id_hewan, jadwal_id):
    # jadwal_id = f"{id_hewan}_{tgl_pemeriksaan_selanjutnya}"
    tgl_pemeriksaan_selanjutnya = jadwal_id.split('_', 1)[1]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan FROM hewan WHERE id = %s", (id_hewan,))
    row = cur.fetchone()
    hewan = None
    if row:
        hewan = {
            'id': row[0],
            'nama': row[1],
            'spesies': row[2],
            'asal_hewan': row[3],
            'tanggal_lahir': row[4],
            'habitat': row[5],
            'status_kesehatan': row[6],
        }
    cur.execute("SELECT id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin FROM jadwal_pemeriksaan_kesehatan WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s", (id_hewan, tgl_pemeriksaan_selanjutnya))
    jadwal_row = cur.fetchone()
    jadwal = None
    if jadwal_row:
        jadwal = {
            'id_hewan': jadwal_row[0],
            'tgl_pemeriksaan_selanjutnya': jadwal_row[1],
            'freq_pemeriksaan_rutin': jadwal_row[2],
            'id': f"{jadwal_row[0]}_{jadwal_row[1]}"
        }
    if request.method == 'POST':
        tgl_pemeriksaan_baru = request.POST.get('tgl_pemeriksaan')
        try:
            cur.execute("UPDATE jadwal_pemeriksaan_kesehatan SET tgl_pemeriksaan_selanjutnya = %s WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s", (tgl_pemeriksaan_baru, id_hewan, tgl_pemeriksaan_selanjutnya))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil diperbarui')
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            messages.error(request, f'Gagal update jadwal: {str(e)}')
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
    cur.close()
    conn.close()
    return render(request, 'penjadwalan/edit_jadwal.html', {'jadwal': jadwal, 'hewan': hewan})

@check_dokter_hewan
def hapus_jadwal_pemeriksaan(request, id_hewan, jadwal_id):
    tgl_pemeriksaan_selanjutnya = jadwal_id.split('_', 1)[1]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan FROM hewan WHERE id = %s", (id_hewan,))
    row = cur.fetchone()
    hewan = None
    if row:
        hewan = {
            'id': row[0],
            'nama': row[1],
            'spesies': row[2],
            'asal_hewan': row[3],
            'tanggal_lahir': row[4],
            'habitat': row[5],
            'status_kesehatan': row[6],
        }
    cur.execute("SELECT id_hewan, tgl_pemeriksaan_selanjutnya, freq_pemeriksaan_rutin FROM jadwal_pemeriksaan_kesehatan WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s", (id_hewan, tgl_pemeriksaan_selanjutnya))
    jadwal_row = cur.fetchone()
    jadwal = None
    if jadwal_row:
        jadwal = {
            'id_hewan': jadwal_row[0],
            'tgl_pemeriksaan_selanjutnya': jadwal_row[1],
            'freq_pemeriksaan_rutin': jadwal_row[2],
            'id': f"{jadwal_row[0]}_{jadwal_row[1]}"
        }
    if request.method == 'POST':
        try:
            cur.execute("DELETE FROM jadwal_pemeriksaan_kesehatan WHERE id_hewan = %s AND tgl_pemeriksaan_selanjutnya = %s", (id_hewan, tgl_pemeriksaan_selanjutnya))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Jadwal pemeriksaan kesehatan berhasil dihapus')
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            messages.error(request, f'Gagal hapus jadwal: {str(e)}')
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
    cur.close()
    conn.close()
    return render(request, 'penjadwalan/hapus_jadwal.html', {'jadwal': jadwal, 'hewan': hewan})

@check_dokter_hewan
def edit_frekuensi_pemeriksaan(request, id_hewan):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nama, spesies, asal_hewan, tanggal_lahir, nama_habitat, status_kesehatan FROM hewan WHERE id = %s", (id_hewan,))
    row = cur.fetchone()
    hewan = None
    if row:
        hewan = {
            'id': row[0],
            'nama': row[1],
            'spesies': row[2],
            'asal_hewan': row[3],
            'tanggal_lahir': row[4],
            'habitat': row[5],
            'status_kesehatan': row[6],
        }
    if request.method == 'POST':
        freq = request.POST.get('freq_pemeriksaan')
        try:
            cur.execute("UPDATE jadwal_pemeriksaan_kesehatan SET freq_pemeriksaan_rutin = %s WHERE id_hewan = %s", (freq, id_hewan))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Frekuensi pemeriksaan rutin berhasil diperbarui')
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            messages.error(request, f'Gagal update frekuensi: {str(e)}')
            return redirect('penjadwalan:list_jadwal_pemeriksaan')
    cur.close()
    conn.close()
    return render(request, 'penjadwalan/edit_frekuensi.html', {'hewan': hewan})
