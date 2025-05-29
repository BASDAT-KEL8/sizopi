import psycopg2
from django.conf import settings
from django.shortcuts import render, redirect
from datetime import date, datetime, timedelta

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

def dashboard_view(request):
    if 'email' not in request.session:
        return redirect('login')
    context = {}
    username = request.session.get('username')
    context['now'] = datetime.now()
    today = date.today()

    conn = get_db_connection()
    cur = conn.cursor()

    # Get user info
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

    # Staf Admin
    cur.execute("SELECT id_staf FROM staf_admin WHERE username_sa = %s", (username,))
    admin = cur.fetchone()
    if admin:
        context['role'] = 'Staf Administrasi'
        context['id_staf'] = admin[0]
        # Example: get ticket sales and visitors for today (replace with your real queries)
        cur.execute("SELECT COALESCE(SUM(jumlah_tiket),0) FROM reservasi WHERE tanggal_kunjungan = %s", (today,))
        context['penjualan_tiket_hari_ini'] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM reservasi WHERE tanggal_kunjungan = %s", (today,))
        context['jumlah_pengunjung_hari_ini'] = cur.fetchone()[0]
        # Pendapatan mingguan dari total kontribusi adopsi 7 hari terakhir
        cur.execute("""
            SELECT COALESCE(SUM(kontribusi_finansial), 0)
            FROM adopsi
            WHERE status_pembayaran = 'Lunas'
              AND tgl_mulai_adopsi >= %s
        """, (today - timedelta(days=7),))
        context['pendapatan_mingguan'] = cur.fetchone()[0]
        cur.close()
        conn.close()
        return render(request, 'dashboard/dashboard.html', context)

    # Dokter Hewan
    cur.execute("SELECT no_str FROM dokter_hewan WHERE username_dh = %s", (username,))
    dokter = cur.fetchone()
    if dokter:
        context['role'] = 'Dokter Hewan'
        context['no_str'] = dokter[0]
        # Spesialisasi
        cur.execute("SELECT nama_spesialisasi FROM spesialisasi WHERE username_sh = %s", (username,))
        context['spesialisasi'] = [row[0] for row in cur.fetchall()]
        # Jumlah hewan ditangani
        cur.execute("SELECT COUNT(DISTINCT id_hewan) FROM catatan_medis WHERE username_dh = %s", (username,))
        context['jumlah_hewan_ditangani'] = cur.fetchone()[0]
        cur.close()
        conn.close()
        return render(request, 'dashboard/dashboard.html', context)

    # Penjaga Hewan
    cur.execute("SELECT id_staf FROM penjaga_hewan WHERE username_jh = %s", (username,))
    penjaga = cur.fetchone()
    if penjaga:
        context['role'] = 'Penjaga Hewan'
        context['id_staf'] = penjaga[0]
        # Jumlah hewan diberi pakan hari ini
        cur.execute("SELECT COUNT(DISTINCT id_hewan) FROM memberi WHERE username_jh = %s", (username,))
        context['jumlah_hewan_diberi_pakan'] = cur.fetchone()[0]
        cur.close()
        conn.close()
        return render(request, 'dashboard/dashboard.html', context)

    # Pelatih Hewan
    cur.execute("SELECT id_staf FROM pelatih_hewan WHERE username_lh = %s", (username,))
    pelatih = cur.fetchone()
    if pelatih:
        context['role'] = 'Staf Pelatih Pertunjukan'
        context['id_staf'] = pelatih[0]
        # Jadwal hari ini
        cur.execute("""
            SELECT jp.tgl_penugasan, jp.nama_atraksi
            FROM jadwal_penugasan jp
            WHERE jp.username_lh = %s AND DATE(jp.tgl_penugasan) = %s
        """, (username, today))
        jadwal_hari_ini = cur.fetchall()
        context['jadwal_hari_ini'] = [
            {'tgl_penugasan': row[0], 'nama_atraksi': {'nama': row[1]}} for row in jadwal_hari_ini
        ]
        # Hewan yang dilatih oleh pelatih ini (berdasarkan semua atraksi yang pernah dijadwalkan)
        cur.execute("""
            SELECT jp.tgl_penugasan, jp.nama_atraksi
            FROM jadwal_penugasan jp
            WHERE jp.username_lh = %s
        """, (username,))
        semua_jadwal = cur.fetchall()
        hewan_dilatih = []
        for row in semua_jadwal:
            tgl_penugasan = row[0]
            nama_atraksi = row[1]
            cur.execute("""
                SELECT h.id, h.nama, h.spesies
                FROM berpartisipasi bp
                JOIN hewan h ON h.id = bp.id_hewan
                WHERE bp.nama_fasilitas = %s
            """, (nama_atraksi,))
            hewan_data = cur.fetchall()
            status_latihan = 'Dalam Pelatihan' if tgl_penugasan.date() == today else 'Selesai'
            if hewan_data:
                for h in hewan_data:
                    hewan_dilatih.append({'id': h[0], 'nama': h[1], 'spesies': h[2], 'nama_atraksi': nama_atraksi, 'tgl_penugasan': tgl_penugasan, 'status_latihan': status_latihan})
            else:
                hewan_dilatih.append({'nama': 'Tidak Ada Data', 'spesies': 'Tidak Ada Data', 'status_latihan': status_latihan, 'nama_atraksi': nama_atraksi, 'tgl_penugasan': tgl_penugasan})
        context['hewan_dilatih'] = hewan_dilatih
        cur.close()
        conn.close()
        return render(request, 'dashboard/dashboard.html', context)

    # Pengunjung
    cur.execute("SELECT alamat, tgl_lahir FROM pengunjung WHERE username_p = %s", (username,))
    pengunjung = cur.fetchone()
    if pengunjung:
        context['role'] = 'Pengunjung'
        context['alamat'] = pengunjung[0]
        context['tanggal_lahir'] = pengunjung[1]
        # Riwayat kunjungan
        cur.execute("""
            SELECT tanggal_kunjungan, nama_atraksi, jumlah_tiket, status
            FROM reservasi
            WHERE username_p = %s AND tanggal_kunjungan < %s
            ORDER BY tanggal_kunjungan DESC LIMIT 10
        """, (username, today))
        context['riwayat_kunjungan'] = [
            {'tanggal_kunjungan': row[0], 'nama_atraksi': row[1], 'jumlah_tiket': row[2], 'status': row[3]} for row in cur.fetchall()
        ]
        # Tiket aktif
        cur.execute("""
            SELECT nama_atraksi, tanggal_kunjungan, jumlah_tiket, status
            FROM reservasi
            WHERE username_p = %s AND tanggal_kunjungan >= %s
            ORDER BY tanggal_kunjungan ASC LIMIT 10
        """, (username, today))
        context['tiket'] = [
            {'nama_atraksi': row[0], 'tanggal_kunjungan': row[1], 'jumlah_tiket': row[2], 'status': row[3]} for row in cur.fetchall()
        ]
        cur.close()
        conn.close()
        return render(request, 'dashboard/dashboard.html', context)

    cur.close()
    conn.close()
    return render(request, 'dashboard/dashboard.html', context)