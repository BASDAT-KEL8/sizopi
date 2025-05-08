from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime
import psycopg2
from django.conf import settings

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

def manage_atraksi(request):
    if 'email' not in request.session:
        return redirect('login')
    
    username = request.session.get('username')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if user is staff admin
    cur.execute("SELECT username_sa FROM staf_admin WHERE username_sa = %s", (username,))
    is_admin = cur.fetchone()
    
    if not is_admin:
        messages.error(request, 'Anda tidak memiliki akses ke halaman ini')
        cur.close()
        conn.close()
        return redirect('dashboard')

    # Get atraksi list with details
    cur.execute("""
        SELECT a.nama_atraksi, a.lokasi, f.kapasitas_max, f.jadwal, 
               array_agg(DISTINCT h.nama) as hewan_names,
               array_agg(DISTINCT h.spesies) as hewan_species,
               p.nama_depan, p.nama_belakang, jp.tgl_penugasan
        FROM atraksi a
        JOIN fasilitas f ON a.nama_atraksi = f.nama
        LEFT JOIN berpartisipasi b ON f.nama = b.nama_fasilitas
        LEFT JOIN hewan h ON b.id_hewan = h.id
        LEFT JOIN jadwal_penugasan jp ON a.nama_atraksi = jp.nama_atraksi 
            AND jp.tgl_penugasan >= NOW()
        LEFT JOIN pelatih_hewan ph ON jp.username_lh = ph.username_lh
        LEFT JOIN pengguna p ON ph.username_lh = p.username
        GROUP BY a.nama_atraksi, a.lokasi, f.kapasitas_max, f.jadwal, p.nama_depan, p.nama_belakang, jp.tgl_penugasan
        ORDER BY a.nama_atraksi
    """)
    atraksi_rows = cur.fetchall()
    
    # Get wahana list with details from fasilitas
    cur.execute("""
        SELECT f.nama, f.kapasitas_max, f.jadwal, w.peraturan
        FROM wahana w
        JOIN fasilitas f ON w.nama_wahana = f.nama
        ORDER BY f.nama
    """)
    wahana_rows = cur.fetchall()
    
    # Format atraksi data
    atraksi_list = []
    for row in atraksi_rows:
        nama, lokasi, kapasitas, jadwal, hewan_names, hewan_species, pelatih_nama_depan, pelatih_nama_belakang, tgl_penugasan = row
        
        # Format hewan list
        hewan_list = []
        if hewan_names[0] is not None:  # Check if there are any animals
            for nama_hewan, spesies in zip(hewan_names, hewan_species):
                hewan_list.append({
                    'id_hewan': {'nama': nama_hewan, 'spesies': spesies}
                })
        
        # Format pelatih info
        pelatih = None
        if pelatih_nama_depan and pelatih_nama_belakang:
            pelatih = {
                'nama': f"{pelatih_nama_depan} {pelatih_nama_belakang}",
                'jadwal': tgl_penugasan
            }
        
        atraksi_list.append({
            'atraksi': {
                'nama': nama,
                'lokasi': lokasi
            },
            'kapasitas_max': kapasitas,
            'jadwal': jadwal,
            'hewan_list': hewan_list,
            'pelatih': pelatih
        })

    # Format wahana data
    wahana_list = [{
        'nama': nama,
        'kapasitas_max': kapasitas,
        'jadwal': jadwal,
        'peraturan': peraturan
    } for nama, kapasitas, jadwal, peraturan in wahana_rows]

    cur.close()
    conn.close()

    context = {
        'atraksi_list': atraksi_list,
        'wahana_list': wahana_list
    }
    return render(request, 'atraksi/manage.html', context)

def tambah_atraksi(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        lokasi = request.POST.get('lokasi')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        pelatih = request.POST.get('pelatih')
        hewan_list = request.POST.getlist('hewan')
        jadwal_pelatih = request.POST.get('jadwal_pelatih')

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Start transaction
            cur.execute("BEGIN")
            
            # Create Fasilitas
            cur.execute(
                "INSERT INTO fasilitas (nama, jadwal, kapasitas_max) VALUES (%s, %s, %s)",
                (nama, jadwal, kapasitas)
            )
            
            # Create Atraksi
            cur.execute(
                "INSERT INTO atraksi (nama_atraksi, lokasi) VALUES (%s, %s)",
                (nama, lokasi)
            )

            # Create Berpartisipasi entries for selected animals
            for hewan_id in hewan_list:
                cur.execute(
                    "INSERT INTO berpartisipasi (nama_fasilitas, id_hewan) VALUES (%s, %s)",
                    (nama, hewan_id)
                )

            # Create JadwalPenugasan for the trainer
            if pelatih and jadwal_pelatih:
                cur.execute(
                    "INSERT INTO jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi) VALUES (%s, %s, %s)",
                    (pelatih, jadwal_pelatih, nama)
                )
            
            # Commit transaction
            cur.execute("COMMIT")
            messages.success(request, 'Atraksi berhasil ditambahkan')
            
        except Exception as e:
            cur.execute("ROLLBACK")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
        
        finally:
            cur.close()
            conn.close()
            
        return redirect('manage_atraksi')
    
    # Get data for form
    conn = get_db_connection()
    cur = conn.cursor()

    # Get trainers
    cur.execute("""
        SELECT ph.username_lh, p.nama_depan, p.nama_belakang
        FROM pelatih_hewan ph
        JOIN pengguna p ON ph.username_lh = p.username
    """)
    pelatih_list = [
        {'username_lh': row[0], 'nama_depan': row[1], 'nama_belakang': row[2]}
        for row in cur.fetchall()
    ]

    # Get animals
    cur.execute("SELECT id, nama, spesies FROM hewan")
    hewan_list = [
        {'id': row[0], 'nama': row[1], 'spesies': row[2]}
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()
    
    context = {
        'pelatih_list': pelatih_list,
        'hewan_list': hewan_list,
    }
    return render(request, 'atraksi/tambah_atraksi.html', context)

def edit_atraksi(request, nama_atraksi):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get atraksi data
    cur.execute("""
        SELECT f.nama, a.lokasi, f.kapasitas_max, f.jadwal
        FROM fasilitas f
        JOIN atraksi a ON f.nama = a.nama_atraksi
        WHERE f.nama = %s
    """, (nama_atraksi,))
    atraksi_data = cur.fetchone()

    if not atraksi_data:
        cur.close()
        conn.close()
        messages.error(request, 'Atraksi tidak ditemukan')
        return redirect('manage_atraksi')

    if request.method == 'POST':
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        pelatih = request.POST.get('pelatih')
        jadwal_pelatih = request.POST.get('jadwal_pelatih')
        hewan_list = request.POST.getlist('hewan')

        try:
            cur.execute("BEGIN")
            
            # Update Fasilitas
            cur.execute(
                "UPDATE fasilitas SET jadwal = %s, kapasitas_max = %s WHERE nama = %s",
                (jadwal, kapasitas, nama_atraksi)
            )

            # Update participating animals
            cur.execute("DELETE FROM berpartisipasi WHERE nama_fasilitas = %s", (nama_atraksi,))
            for hewan_id in hewan_list:
                cur.execute(
                    "INSERT INTO berpartisipasi (nama_fasilitas, id_hewan) VALUES (%s, %s)",
                    (nama_atraksi, hewan_id)
                )

            # Update trainer schedule
            cur.execute("DELETE FROM jadwal_penugasan WHERE nama_atraksi = %s", (nama_atraksi,))
            if pelatih and jadwal_pelatih:
                cur.execute(
                    "INSERT INTO jadwal_penugasan (username_lh, tgl_penugasan, nama_atraksi) VALUES (%s, %s, %s)",
                    (pelatih, jadwal_pelatih, nama_atraksi)
                )

            cur.execute("COMMIT")
            messages.success(request, 'Atraksi berhasil diperbarui')
            
        except Exception as e:
            cur.execute("ROLLBACK")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            
        finally:
            cur.close()
            conn.close()
            
        return redirect('manage_atraksi')

    # Get current data for form
    # Get participating animals
    cur.execute("""
        SELECT h.id, h.nama, h.spesies
        FROM berpartisipasi b
        JOIN hewan h ON b.id_hewan = h.id
        WHERE b.nama_fasilitas = %s
    """, (nama_atraksi,))
    current_animals = [
        {'id_hewan': {'id': row[0], 'nama': row[1], 'spesies': row[2]}}
        for row in cur.fetchall()
    ]

    # Get current schedule
    cur.execute("""
        SELECT jp.username_lh, jp.tgl_penugasan, p.nama_depan, p.nama_belakang
        FROM jadwal_penugasan jp
        JOIN pelatih_hewan ph ON jp.username_lh = ph.username_lh
        JOIN pengguna p ON ph.username_lh = p.username
        WHERE jp.nama_atraksi = %s
        ORDER BY jp.tgl_penugasan DESC
        LIMIT 1
    """, (nama_atraksi,))
    current_schedule = cur.fetchone()

    # Get all trainers and animals for form options
    cur.execute("""
        SELECT ph.username_lh, p.nama_depan, p.nama_belakang
        FROM pelatih_hewan ph
        JOIN pengguna p ON ph.username_lh = p.username
    """)
    pelatih_list = [
        {'username_lh': row[0], 'nama_depan': row[1], 'nama_belakang': row[2]}
        for row in cur.fetchall()
    ]

    cur.execute("SELECT id, nama, spesies FROM hewan")
    hewan_list = [
        {'id': row[0], 'nama': row[1], 'spesies': row[2]}
        for row in cur.fetchall()
    ]

    cur.close()
    conn.close()

    context = {
        'atraksi': {
            'nama_atraksi': {'nama': atraksi_data[0]},
            'lokasi': atraksi_data[1],
            'nama_atraksi.kapasitas_max': atraksi_data[2],
            'nama_atraksi.jadwal': atraksi_data[3]
        },
        'pelatih_list': pelatih_list,
        'hewan_list': hewan_list,
        'current_animals': current_animals,
        'current_schedule': {
            'username_lh': current_schedule[0],
            'tgl_penugasan': current_schedule[1],
            'nama_depan': current_schedule[2],
            'nama_belakang': current_schedule[3]
        } if current_schedule else None
    }
    return render(request, 'atraksi/edit_atraksi.html', context)

def hapus_atraksi(request, nama_atraksi):
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN")
            
            # Delete related records first
            cur.execute("DELETE FROM jadwal_penugasan WHERE nama_atraksi = %s", (nama_atraksi,))
            cur.execute("DELETE FROM berpartisipasi WHERE nama_fasilitas = %s", (nama_atraksi,))
            cur.execute("DELETE FROM atraksi WHERE nama_atraksi = %s", (nama_atraksi,))
            cur.execute("DELETE FROM fasilitas WHERE nama = %s", (nama_atraksi,))
            
            cur.execute("COMMIT")
            messages.success(request, 'Atraksi berhasil dihapus')
            
        except Exception as e:
            cur.execute("ROLLBACK")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            
        finally:
            cur.close()
            conn.close()
            
        return redirect('manage_atraksi')
    
    return render(request, 'atraksi/hapus_atraksi.html', {'nama_atraksi': nama_atraksi})

# Similar functions for Wahana
def tambah_wahana(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        peraturan = request.POST.get('peraturan')

        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN")
            
            # Create Fasilitas
            cur.execute(
                "INSERT INTO fasilitas (nama, jadwal, kapasitas_max) VALUES (%s, %s, %s)",
                (nama, jadwal, kapasitas)
            )
            
            # Create Wahana
            cur.execute(
                "INSERT INTO wahana (nama_wahana, peraturan) VALUES (%s, %s)",
                (nama, peraturan)
            )
            
            cur.execute("COMMIT")
            messages.success(request, 'Wahana berhasil ditambahkan')
            
        except Exception as e:
            cur.execute("ROLLBACK")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            
        finally:
            cur.close()
            conn.close()
            
        return redirect('manage_atraksi')
        
    return render(request, 'atraksi/tambah_wahana.html')

def edit_wahana(request, nama_wahana):
    conn = get_db_connection()
    cur = conn.cursor()

    # Get wahana data
    cur.execute("""
        SELECT f.nama, f.kapasitas_max, f.jadwal, w.peraturan
        FROM fasilitas f
        JOIN wahana w ON f.nama = w.nama_wahana
        WHERE f.nama = %s
    """, (nama_wahana,))
    wahana_data = cur.fetchone()

    if not wahana_data:
        cur.close()
        conn.close()
        messages.error(request, 'Wahana tidak ditemukan')
        return redirect('manage_atraksi')

    if request.method == 'POST':
        kapasitas = request.POST.get('kapasitas')
        jadwal = request.POST.get('jadwal')
        peraturan = request.POST.get('peraturan')

        try:
            cur.execute("BEGIN")
            
            # Update Fasilitas
            cur.execute(
                "UPDATE fasilitas SET jadwal = %s, kapasitas_max = %s WHERE nama = %s",
                (jadwal, kapasitas, nama_wahana)
            )
            
            # Update Wahana
            cur.execute(
                "UPDATE wahana SET peraturan = %s WHERE nama_wahana = %s",
                (peraturan, nama_wahana)
            )
            
            cur.execute("COMMIT")
            messages.success(request, 'Wahana berhasil diperbarui')
            
        except Exception as e:
            cur.execute("ROLLBACK")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            
        finally:
            cur.close()
            conn.close()
            
        return redirect('manage_atraksi')

    context = {
        'wahana': {
            'nama_wahana': {'nama': wahana_data[0]},
            'nama_wahana.kapasitas_max': wahana_data[1],
            'nama_wahana.jadwal': wahana_data[2],
            'peraturan': wahana_data[3]
        }
    }
    cur.close()
    conn.close()
    return render(request, 'atraksi/edit_wahana.html', context)

def hapus_wahana(request, nama_wahana):
    if request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            cur.execute("BEGIN")
            
            # Delete Wahana and Fasilitas
            cur.execute("DELETE FROM wahana WHERE nama_wahana = %s", (nama_wahana,))
            cur.execute("DELETE FROM fasilitas WHERE nama = %s", (nama_wahana,))
            
            cur.execute("COMMIT")
            messages.success(request, 'Wahana berhasil dihapus')
            
        except Exception as e:
            cur.execute("ROLLBACK")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
            
        finally:
            cur.close()
            conn.close()
            
        return redirect('manage_atraksi')
    
    return render(request, 'atraksi/hapus_wahana.html', {'nama_wahana': nama_wahana})
