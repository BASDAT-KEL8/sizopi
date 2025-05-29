from django.shortcuts import render, redirect
from django.contrib import messages
import psycopg2
from datetime import datetime, date, timedelta
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

def index(request):
    if 'username' not in request.session:
        return redirect('login')
        
    username = request.session.get('username')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check user role
    cur.execute("SELECT username_sa FROM staf_admin WHERE username_sa = %s", (username,))
    is_staff = cur.fetchone() is not None

    # Ambil tanggal dari GET, default hari ini
    selected_date = request.GET.get('tanggal')
    if selected_date:
        try:
            tanggal_filter = datetime.strptime(selected_date, '%Y-%m-%d').date()
        except ValueError:
            tanggal_filter = date.today()
    else:
        tanggal_filter = date.today()
    
    # Get available atraksi and wahana with remaining capacity
    available_atraksi = []
    available_wahana = []
    if not is_staff:
        # Get available atraksi
        cur.execute("""
            WITH booked_capacity AS (
                SELECT nama_atraksi, tanggal_kunjungan::date, SUM(jumlah_tiket) as total_booked
                FROM reservasi 
                WHERE tanggal_kunjungan::date = %s
                GROUP BY nama_atraksi, tanggal_kunjungan::date
            )
            SELECT 
                a.nama_atraksi as nama,
                f.jadwal,
                f.kapasitas_max,
                COALESCE(f.kapasitas_max - COALESCE(bc.total_booked, 0), f.kapasitas_max) as kapasitas_tersedia
            FROM atraksi a
            JOIN fasilitas f ON a.nama_atraksi = f.nama
            LEFT JOIN booked_capacity bc ON a.nama_atraksi = bc.nama_atraksi
            ORDER BY f.jadwal
        """, [tanggal_filter])
        available_atraksi = [{
            'id': row[0],
            'nama': row[0],
            'jadwal': row[1],
            'kapasitas_max': row[2],
            'kapasitas_tersedia': row[3]
        } for row in cur.fetchall()]

        # Get available wahana
        cur.execute("""
            WITH booked_capacity AS (
                SELECT w.nama_wahana, r.tanggal_kunjungan::date, SUM(r.jumlah_tiket) as total_booked
                FROM wahana w
                LEFT JOIN reservasi r ON w.nama_wahana = r.nama_atraksi AND r.tanggal_kunjungan::date = %s
                GROUP BY w.nama_wahana, r.tanggal_kunjungan::date
            )
            SELECT 
                w.nama_wahana as nama,
                f.jadwal,
                f.kapasitas_max,
                COALESCE(f.kapasitas_max - COALESCE(bc.total_booked, 0), f.kapasitas_max) as kapasitas_tersedia
            FROM wahana w
            JOIN fasilitas f ON w.nama_wahana = f.nama
            LEFT JOIN booked_capacity bc ON w.nama_wahana = bc.nama_wahana
            ORDER BY f.jadwal
        """, [tanggal_filter])
        available_wahana = [{
            'id': row[0],
            'nama': row[0],
            'jadwal': row[1],
            'kapasitas_max': row[2],
            'kapasitas_tersedia': row[3]
        } for row in cur.fetchall()]
    
    # Get reservations based on role
    if is_staff:
        cur.execute("""
            SELECT r.username_p, r.nama_atraksi, r.tanggal_kunjungan, r.jumlah_tiket, r.status,
                   r.nama_atraksi || '_' || r.username_p || '_' || r.tanggal_kunjungan::text || '_' || r.jumlah_tiket::text as id
            FROM reservasi r
            ORDER BY r.tanggal_kunjungan DESC
        """)
    else:
        cur.execute("""
            SELECT r.username_p, r.nama_atraksi, r.tanggal_kunjungan, r.jumlah_tiket, r.status,
                   r.nama_atraksi || '_' || r.username_p || '_' || r.tanggal_kunjungan::text || '_' || r.jumlah_tiket::text as id
            FROM reservasi r
            WHERE r.username_p = %s
            ORDER BY r.tanggal_kunjungan DESC
        """, [username])
    
    # Format reservations data
    reservations = []
    for row in cur.fetchall():
        reservations.append({
            'username_pengunjung': row[0],
            'nama_atraksi': row[1],
            'tanggal_reservasi': row[2],
            'jumlah_tiket': row[3],
            'status': row[4],
            'id': row[5]
        })
    
    cur.close()
    conn.close()
    
    context = {
        'available_atraksi': available_atraksi if not is_staff else [],
        'available_wahana': available_wahana if not is_staff else [],
        'reservations': reservations,
        'is_staff': is_staff,
        'selected_date': tanggal_filter,
        'today': date.today(),
    }
    return render(request, 'booking/index.html', context)

def create_reservation(request):
    if 'username' not in request.session:
        return redirect('login')
        
    username = request.session.get('username')
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check if user is staff admin
    cur.execute("SELECT username_sa FROM staf_admin WHERE username_sa = %s", (username,))
    if cur.fetchone():
        messages.error(request, 'Staff admin tidak diizinkan membuat reservasi')
        cur.close()
        conn.close()
        return redirect('booking_index')
    
    prefill_nama_atraksi = request.GET.get('id')
    prefill_lokasi = None
    prefill_jam = None
    prefill_peraturan = None
    tipe_form = None
    # --- Pindahkan logika prefill & tipe sebelum cur.close() ---
    if prefill_nama_atraksi:
        cur2 = conn.cursor()
        cur2.execute("SELECT 1 FROM atraksi WHERE nama_atraksi = %s", (prefill_nama_atraksi,))
        if cur2.fetchone():
            tipe_form = 'atraksi'
            cur2.execute("SELECT lokasi FROM atraksi WHERE nama_atraksi = %s", (prefill_nama_atraksi,))
            row = cur2.fetchone()
            if row:
                prefill_lokasi = row[0]
            cur2.execute("SELECT jadwal FROM fasilitas WHERE nama = %s", (prefill_nama_atraksi,))
            row2 = cur2.fetchone()
            if row2:
                prefill_jam = row2[0]
        else:
            tipe_form = 'wahana'
            cur2.execute("SELECT peraturan FROM wahana WHERE nama_wahana = %s", (prefill_nama_atraksi,))
            row = cur2.fetchone()
            if row:
                prefill_peraturan = row[0]
            cur2.execute("SELECT jadwal FROM fasilitas WHERE nama = %s", (prefill_nama_atraksi,))
            row2 = cur2.fetchone()
            if row2:
                prefill_jam = row2[0]
        cur2.close()
    if request.method == 'POST':
        nama_atraksi = request.POST.get('nama_atraksi')
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))

        # Cek apakah nama_atraksi adalah atraksi
        cur.execute("SELECT 1 FROM atraksi WHERE nama_atraksi = %s", (nama_atraksi,))
        is_atraksi = cur.fetchone() is not None
        if is_atraksi:
            cur.execute("""
                SELECT f.kapasitas_max
                FROM fasilitas f
                JOIN atraksi a ON f.nama = a.nama_atraksi
                WHERE f.nama = %s
            """, (nama_atraksi,))
        else:
            cur.execute("""
                SELECT f.kapasitas_max
                FROM fasilitas f
                JOIN wahana w ON f.nama = w.nama_wahana
                WHERE f.nama = %s
            """, (nama_atraksi,))
        facility = cur.fetchone()
        if not facility:
            messages.error(request, f'Atraksi/Wahana "{nama_atraksi}" tidak ditemukan di database. Pastikan nama sesuai dengan data di tabel fasilitas/wahana.')
            status = 'Gagal'
        else:
            try:
                cur.execute("BEGIN")
                cur.execute("""
                    INSERT INTO reservasi (username_p, nama_atraksi, tanggal_kunjungan, jumlah_tiket, status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (username, nama_atraksi, tanggal, jumlah_tiket, 'Terjadwal'))
                cur.execute("COMMIT")
                messages.success(request, 'Reservasi berhasil dibuat!')
                cur.close()
                conn.close()
                return redirect('booking_index')
            except psycopg2.Error as e:
                cur.execute("ROLLBACK")
                error_msg = str(e)
                # Remove 'CONTEXT: ...' from error message if present
                if 'CONTEXT:' in error_msg:
                    error_msg = error_msg.split('CONTEXT:')[0].strip()
                # Tangkap pesan error dari trigger kapasitas
                if 'Kapasitas tersisa' in error_msg:
                    messages.error(request, error_msg)
                else:
                    messages.error(request, f'Terjadi kesalahan: {error_msg}')
                status = 'Gagal'
        # Render detail view
        # return render(request, 'booking/detail_reservation.html', {...})
    
    # Get list of available attractions and wahana (tambahkan peraturan untuk wahana)
    cur.execute("""
        SELECT a.nama_atraksi, a.lokasi, f.jadwal, f.kapasitas_max, 'atraksi' as tipe, NULL as peraturan
        FROM atraksi a
        JOIN fasilitas f ON a.nama_atraksi = f.nama
        UNION ALL
        SELECT w.nama_wahana, '' as lokasi, f.jadwal, f.kapasitas_max, 'wahana' as tipe, w.peraturan
        FROM wahana w
        JOIN fasilitas f ON w.nama_wahana = f.nama
    """)
    attractions = [
        {
            'nama': row[0],
            'lokasi': row[1],
            'jam': row[2],
            'kapasitas': row[3],
            'tipe': row[4],
            'peraturan': row[5]
        } for row in cur.fetchall()
    ]
    cur.close()
    conn.close()
    if tipe_form == 'wahana':
        template_name = 'booking/create_reservation_wahana.html'
    else:
        template_name = 'booking/create_reservation_atraksi.html'
    return render(request, template_name, {
        'attractions': attractions,
        'prefill_nama_atraksi': prefill_nama_atraksi,
        'prefill_lokasi': prefill_lokasi,
        'prefill_jam': prefill_jam,
        'prefill_peraturan': prefill_peraturan
    })

def edit_reservation(request, id):
    if 'username' not in request.session:
        return redirect('login')
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Parse composite key
    try:
        nama_atraksi, username_p, tanggal_str, jumlah_tiket = id.split('_')
    except:
        messages.error(request, 'Format ID reservasi tidak valid')
        return redirect('booking_index')
    
    # Get reservation details
    cur.execute("""
        SELECT r.username_p, r.nama_atraksi, r.tanggal_kunjungan, r.jumlah_tiket, r.status,
               a.lokasi, f.jadwal
        FROM reservasi r
        JOIN atraksi a ON r.nama_atraksi = a.nama_atraksi
        JOIN fasilitas f ON a.nama_atraksi = f.nama
        WHERE r.nama_atraksi = %s 
        AND r.username_p = %s
        AND r.tanggal_kunjungan::text = %s
        AND r.jumlah_tiket::text = %s
    """, (nama_atraksi, username_p, tanggal_str, jumlah_tiket))
    
    reservation = cur.fetchone()
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        cur.close()
        conn.close()
        return redirect('booking_index')
    
    if request.method == 'POST':
        nama_atraksi = request.POST.get('nama_atraksi')
        tanggal = request.POST.get('tanggal')
        jumlah_tiket = int(request.POST.get('jumlah_tiket'))
        
        # Check capacity from fasilitas table
        cur.execute("""
            SELECT kapasitas_max
            FROM fasilitas
            WHERE nama = %s
        """, (nama_atraksi,))
        
        kapasitas = cur.fetchone()[0]
        if jumlah_tiket <= kapasitas:
            try:
                cur.execute("BEGIN")
                cur.execute("""
                    UPDATE reservasi 
                    SET nama_atraksi = %s, tanggal_kunjungan = %s, jumlah_tiket = %s
                    WHERE nama_atraksi = %s AND username_p = %s AND tanggal_kunjungan::text = %s AND jumlah_tiket::text = %s
                """, (nama_atraksi, tanggal, jumlah_tiket, reservation[1], reservation[0], str(reservation[2]), str(reservation[3])))
                cur.execute("COMMIT")
                messages.success(request, 'Reservasi berhasil diperbarui!')
                
                # Get updated attraction info
                cur.execute("""
                    SELECT a.lokasi, f.jadwal
                    FROM atraksi a
                    JOIN fasilitas f ON a.nama_atraksi = f.nama
                    WHERE a.nama_atraksi = %s
                """, (nama_atraksi,))
                attr_info = cur.fetchone()
                
                cur.close()
                conn.close()
                return render(request, 'booking/detail_reservation.html', {
                    'id': id,
                    'nama_atraksi': nama_atraksi,
                    'lokasi': attr_info[0],
                    'jam': attr_info[1],
                    'tanggal': tanggal,
                    'jumlah_tiket': jumlah_tiket,
                    'status': reservation[4]
                })
            except Exception as e:
                cur.execute("ROLLBACK")
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
        else:
            messages.error(request, 'Update gagal: Kapasitas tidak mencukupi')
    
    # Get list of attractions for form
    cur.execute("""
        SELECT a.nama_atraksi, a.lokasi, f.jadwal, f.kapasitas_max
        FROM atraksi a
        JOIN fasilitas f ON a.nama_atraksi = f.nama
    """)
    attractions = [
        {
            'nama': row[0],
            'lokasi': row[1],
            'jam': row[2],
            'kapasitas': row[3]
        } for row in cur.fetchall()
    ]
    
    context = {
        'reservation': {
            'nama_atraksi': reservation[1],
            'tanggal_reservasi': reservation[2],
            'jumlah_tiket': reservation[3],
            'status': reservation[4]
        },
        'attractions': attractions,
        'nama_atraksi': reservation[1]
    }
    
    cur.close()
    conn.close()
    return render(request, 'booking/edit_reservation.html', context)

def detail_reservation(request, id):
    if 'username' not in request.session:
        return redirect('login')
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Parse composite key
    try:
        nama_atraksi, username_p, tanggal_str, jumlah_tiket = id.split('_')
    except:
        messages.error(request, 'Format ID reservasi tidak valid')
        return redirect('booking_index')
        
    cur.execute("""
        SELECT r.nama_atraksi, r.tanggal_kunjungan, r.jumlah_tiket, r.status,
               COALESCE(a.lokasi, '') as lokasi, f.jadwal, w.peraturan
        FROM reservasi r
        LEFT JOIN atraksi a ON r.nama_atraksi = a.nama_atraksi
        LEFT JOIN wahana w ON r.nama_atraksi = w.nama_wahana
        JOIN fasilitas f ON r.nama_atraksi = f.nama
        WHERE r.nama_atraksi = %s 
        AND r.username_p = %s
        AND r.tanggal_kunjungan::text = %s
        AND r.jumlah_tiket::text = %s
    """, (nama_atraksi, username_p, tanggal_str, jumlah_tiket))
    reservation = cur.fetchone()
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        cur.close()
        conn.close()
        return redirect('booking_index')
    context = {
        'id': id,
        'nama_atraksi': reservation[0],
        'lokasi': reservation[4],
        'jam': reservation[5],
        'tanggal': reservation[1],
        'jumlah_tiket': reservation[2],
        'status': reservation[3],
        'peraturan': reservation[6]
    }
    
    cur.close()
    conn.close()
    return render(request, 'booking/detail_reservation.html', context)

def cancel_reservation(request, id):
    if 'username' not in request.session:
        return redirect('login')
        
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Parse composite key
    try:
        nama_atraksi, username_p, tanggal_str, jumlah_tiket = id.split('_')
    except:
        messages.error(request, 'Format ID reservasi tidak valid')
        return redirect('booking_index')
    
    # Get reservation details for confirmation
    cur.execute("""
        SELECT r.nama_atraksi, r.tanggal_kunjungan, r.jumlah_tiket,
               COALESCE(a.lokasi, '') as lokasi, f.jadwal, w.peraturan
        FROM reservasi r
        LEFT JOIN atraksi a ON r.nama_atraksi = a.nama_atraksi
        LEFT JOIN wahana w ON r.nama_atraksi = w.nama_wahana
        JOIN fasilitas f ON r.nama_atraksi = f.nama
        WHERE r.nama_atraksi = %s 
        AND r.username_p = %s
        AND r.tanggal_kunjungan::text = %s
        AND r.jumlah_tiket::text = %s
    """, (nama_atraksi, username_p, tanggal_str, jumlah_tiket))
    
    reservation = cur.fetchone()
    if not reservation:
        messages.error(request, 'Reservasi tidak ditemukan')
        cur.close()
        conn.close()
        return redirect('booking_index')
    
    if request.method == 'POST':
        try:
            cur.execute("BEGIN")
            cur.execute("""
                UPDATE reservasi SET status = 'Dibatalkan'
                WHERE nama_atraksi = %s AND username_p = %s AND tanggal_kunjungan::text = %s AND jumlah_tiket::text = %s
            """, (nama_atraksi, username_p, tanggal_str, jumlah_tiket))
            cur.execute("COMMIT")
            messages.success(request, 'Reservasi berhasil dibatalkan')
            cur.close()
            conn.close()
            return redirect('booking_index')
        except Exception as e:
            cur.execute("ROLLBACK")
            messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    context = {
        'reservation': {
            'nama_atraksi': reservation[0],
            'tanggal_reservasi': reservation[1],
            'jumlah_tiket': reservation[2]
        },
        'attraction': {
            'lokasi': reservation[3],
            'jam': reservation[4],
            'peraturan': reservation[5]
        }
    }
    
    cur.close()
    conn.close()
    return render(request, 'booking/cancel_reservation.html', context)
