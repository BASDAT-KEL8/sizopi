import uuid
from django.contrib import messages
from django.conf import settings
from django.db import connection
import psycopg2
from django.shortcuts import render, redirect


def is_dokter_hewan(request):
    username = request.session.get('username')
    if not username:
        return False
    conn = connection
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM dokter_hewan WHERE username_dh = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return bool(result)

def is_penjaga_hewan(request):
    username = request.session.get('username')
    if not username:
        return False
    conn = connection
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM penjaga_hewan WHERE username_dh = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return bool(result)

def is_staff_admin(request):
    username = request.session.get('username')
    if not username:
        return False
    conn = connection
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM staff_admin WHERE username_dh = %s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return bool(result)


def get_connection():
    return psycopg2.connect(
        dbname=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD'],
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        sslmode='require',
        options='-c search_path=sizopi'
    )

def get_user_role(request):
    username = request.session.get('username')
    if not username:
        return ""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM dokter_hewan WHERE username_dh = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return 'Dokter Hewan'

    cur.execute("SELECT 1 FROM penjaga_hewan WHERE username_jh = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return 'Penjaga Hewan'

    cur.execute("SELECT 1 FROM staf_admin WHERE username_sa = %s", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return 'Staf Administrasi'

    cur.close()
    conn.close()
    return ""

def view_satwa(request):
    if not is_dokter_hewan(request) or not is_penjaga_hewan(request) or not is_staff_admin(request):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
        FROM HEWAN ORDER BY nama
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    satwa_list = [{
        "id": row[0], "nama": row[1], "spesies": row[2], "asal": row[3],
        "tanggal_lahir": row[4], "status": row[5], "habitat": row[6], "foto": row[7]
    } for row in rows]

    return render(request, 'view_satwa.html', {
        "satwa_list": satwa_list, 
        "user_role": get_user_role(request)
    })

def create_satwa(request):
    if not is_dokter_hewan(request) or not is_penjaga_hewan(request) or not is_staff_admin(request):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    if request.method == "POST":
        nama = request.POST.get("nama")
        spesies = request.POST.get("spesies")
        asal = request.POST.get("asal")
        tanggal = request.POST.get("tanggal_lahir") or None
        status = request.POST.get("status")
        habitat = request.POST.get("habitat")
        url_foto = request.POST.get("foto")
        id_baru = str(uuid.uuid4())

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO HEWAN (id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (id_baru, nama, spesies, asal, tanggal, status, habitat, url_foto))
        conn.commit()
        cur.close()
        conn.close()
        return redirect('satwa:view_satwa')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT nama FROM HABITAT ORDER BY nama")
    habitat_options = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    return render(request, 'create_satwa.html', {
        "habitat_options": habitat_options,
        "user_role": get_user_role(request)
    })

def delete_satwa(request, id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM HEWAN WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('satwa:view_satwa')

def edit_satwa(request, id):
    if not is_dokter_hewan(request) or not is_penjaga_hewan(request) or not is_staff_admin(request):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    if request.method == "POST":
        nama = request.POST.get("nama")
        spesies = request.POST.get("spesies")
        asal = request.POST.get("asal")
        tanggal = request.POST.get("tanggal_lahir") or None
        status = request.POST.get("status")
        habitat = request.POST.get("habitat")
        foto = request.POST.get("foto")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE HEWAN SET nama = %s, spesies = %s, asal_hewan = %s, tanggal_lahir = %s,
            status_kesehatan = %s, nama_habitat = %s, url_foto = %s WHERE id = %s
        """, (nama, spesies, asal, tanggal, status, habitat, foto, id))
        conn.commit()
        cur.close()
        conn.close()

        return redirect('satwa:view_satwa')

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
        FROM HEWAN WHERE id = %s
    """, (id,))
    data = cur.fetchone()

    cur.execute("SELECT nama FROM HABITAT ORDER BY nama")
    habitat_options = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    return render(request, 'edit_satwa.html', {
        "satwa": {
            "id": data[0], "nama": data[1], "spesies": data[2], "asal": data[3],
            "tanggal_lahir": data[4], "status": data[5], "habitat": data[6], "foto": data[7]
        },
        "habitat_options": habitat_options,
        "user_role": get_user_role(request)
    })