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

def is_penjaga_hewan(request):
    username = request.session.get('username')
    if not username:
        return False
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM penjaga_hewan WHERE username_jh = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return bool(result)

def check_penjaga_hewan(view_func):
    def wrapper(request, *args, **kwargs):
        if not is_penjaga_hewan(request):
            messages.error(request, 'Hanya penjaga hewan yang dapat mengakses fitur ini.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

@check_penjaga_hewan
def list_pemberian_pakan(request, id_hewan):
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
    cur.execute("SELECT jadwal, jenis, jumlah, status FROM pakan WHERE id_hewan = %s ORDER BY jadwal DESC", (id_hewan,))
    pakan_list = [
        {
            'id_hewan': id_hewan,
            'jadwal': row[0],
            'jenis': row[1],
            'jumlah': row[2],
            'status': row[3],
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    context = {
        'hewan': hewan,
        'pakan_list': pakan_list
    }
    return render(request, 'pakan/list_pemberian_pakan.html', context)

@check_penjaga_hewan
def tambah_jadwal_pakan(request, id_hewan):
    if request.method == 'POST':
        jenis = request.POST.get('jenis')
        jumlah = request.POST.get('jumlah')
        jadwal = request.POST.get('jadwal')
        status = 'dijadwalkan'  # harus sama dengan di database
        username = request.session.get('username')
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Tambah ke tabel pakan
            cur.execute("INSERT INTO pakan (id_hewan, jadwal, jenis, jumlah, status) VALUES (%s, %s, %s, %s, %s)", (id_hewan, jadwal, jenis, jumlah, status))
            # Tambah ke tabel memberi
            cur.execute("INSERT INTO memberi (id_hewan, jadwal, username_jh) VALUES (%s, %s, %s)", (id_hewan, jadwal, username))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Jadwal pemberian pakan berhasil ditambahkan')
            return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            messages.error(request, f'Gagal menambah jadwal: {str(e)}')
            return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
    return render(request, 'pakan/tambah_pakan.html', {'id_hewan': id_hewan})


@check_penjaga_hewan
def hapus_pemberian_pakan(request, id_hewan, jadwal):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT jadwal, jenis, jumlah, status FROM pakan WHERE id_hewan = %s AND jadwal = %s", (id_hewan, jadwal))
    row = cur.fetchone()
    pakan = None
    if row:
        pakan = {
            'id_hewan': id_hewan,
            'jadwal': row[0],
            'jenis': row[1],
            'jumlah': row[2],
            'status': row[3],
        }
    if request.method == 'POST':
        try:
            cur.execute("DELETE FROM pakan WHERE id_hewan = %s AND jadwal = %s", (id_hewan, jadwal))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Data pemberian pakan berhasil dihapus')
            return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            messages.error(request, f'Gagal hapus data: {str(e)}')
            return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
    cur.close()
    conn.close()
    return render(request, 'pakan/hapus_pakan.html', {'pakan': pakan, 'id_hewan': id_hewan})

@check_penjaga_hewan
def beri_pakan(request, id_hewan, jadwal):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE pakan SET status = 'diberikan' WHERE id_hewan = %s AND jadwal = %s AND status = 'dijadwalkan'", (id_hewan, jadwal))
        conn.commit()
        cur.close()
        conn.close()
        messages.success(request, 'Pemberian pakan berhasil dicatat')
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        messages.error(request, f'Gagal mencatat pemberian pakan: {str(e)}')
    return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)

@check_penjaga_hewan
def riwayat_pemberian_pakan(request):
    username = request.session.get('username')
    if not username:
        messages.error(request, 'Silakan login terlebih dahulu.')
        return redirect('login')
    conn = get_db_connection()
    cur = conn.cursor()
    # Ambil semua jadwal pakan yang pernah diberikan oleh user ini dari tabel memberi
    cur.execute("SELECT id_hewan, jadwal FROM memberi WHERE username_jh = %s", (username,))
    jadwal_list = cur.fetchall()
    riwayat_pakan = []
    if jadwal_list:
        for id_hewan, jadwal in jadwal_list:
            # Ambil data pakan (apapun statusnya) yang diberikan user ini
            cur.execute("SELECT jenis, jumlah, status FROM pakan WHERE id_hewan = %s AND jadwal = %s", (id_hewan, jadwal))
            pakan_row = cur.fetchone()
            if pakan_row:
                jenis, jumlah, status = pakan_row
                # Ambil data hewan
                cur.execute("SELECT nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat FROM hewan WHERE id = %s", (id_hewan,))
                h = cur.fetchone()
                hewan = None
                if h:
                    hewan = {
                        'nama': h[0],
                        'spesies': h[1],
                        'asal_hewan': h[2],
                        'tanggal_lahir': h[3],
                        'status_kesehatan': h[4],
                        'habitat': h[5],
                    }
                riwayat_pakan.append({
                    'hewan': hewan,
                    'jenis': jenis,
                    'jumlah': jumlah,
                    'jadwal': jadwal,
                    'status': status,
                })
    cur.close()
    conn.close()
    context = {
        'riwayat_pakan': riwayat_pakan
    }
    return render(request, 'pakan/riwayat_pemberian_pakan.html', context)

@check_penjaga_hewan
def list_hewan_pakan(request):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nama, spesies, nama_habitat FROM hewan ORDER BY nama ASC")
    hewan_list = [
        {
            'id': row[0],
            'nama': row[1],
            'spesies': row[2],
            'habitat': row[3],
        }
        for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    return render(request, 'pakan/list_hewan_pakan.html', {'hewan_list': hewan_list})

@check_penjaga_hewan
def edit_pemberian_pakan(request, id_hewan, jadwal):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT jadwal, jenis, jumlah, status FROM pakan WHERE id_hewan = %s AND jadwal = %s", (id_hewan, jadwal))
    row = cur.fetchone()
    pakan = None
    if row:
        pakan = {
            'id_hewan': id_hewan,
            'jadwal': row[0],
            'jenis': row[1],
            'jumlah': row[2],
            'status': row[3],
        }
    if not pakan:
        cur.close()
        conn.close()
        messages.error(request, 'Data pakan tidak ditemukan.')
        return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
    if request.method == 'POST':
        jenis = request.POST.get('jenis_pakan')
        jumlah = request.POST.get('jumlah_pakan')
        jadwal_baru = request.POST.get('jadwal')
        status = request.POST.get('status') or pakan['status']
        if not jenis or not jumlah or not jadwal_baru or not status:
            messages.error(request, 'Semua field harus diisi!')
            cur.close()
            conn.close()
            return render(request, 'pakan/edit_pakan.html', {'pakan': pakan, 'id_hewan': id_hewan})
        try:
            # Jika jadwal berubah, update tabel memberi dulu baru pakan
            if jadwal_baru != str(jadwal):
                cur.execute("UPDATE memberi SET jadwal = %s WHERE id_hewan = %s AND jadwal = %s", (jadwal_baru, id_hewan, jadwal))
            cur.execute("UPDATE pakan SET jenis = %s, jumlah = %s, jadwal = %s, status = %s WHERE id_hewan = %s AND jadwal = %s", (jenis, jumlah, jadwal_baru, status, id_hewan, jadwal))
            conn.commit()
            cur.close()
            conn.close()
            messages.success(request, 'Data pemberian pakan berhasil diubah')
            return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
        except Exception as e:
            conn.rollback()
            cur.close()
            conn.close()
            messages.error(request, f'Gagal mengubah data: {str(e)}')
            return redirect('pakan:list_pemberian_pakan', id_hewan=id_hewan)
    cur.close()
    conn.close()
    return render(request, 'pakan/edit_pakan.html', {'pakan': pakan, 'id_hewan': id_hewan})
