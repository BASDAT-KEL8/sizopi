from django.contrib import messages
from django.shortcuts import redirect, render
from django.db import connection

def is_penjaga_hewan(request):
    username = request.session.get('username')
    if not username:
        return False
    conn = connection
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM penjaga_hewan WHERE username_jh = %s", (username,))
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
    cur.execute("SELECT 1 FROM staf_admin WHERE username_sa =%s", (username,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return bool(result)

def get_user_role(request):
    username = request.session.get('username')
    if not username:
        return ""

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1 FROM penjaga_hewan WHERE username_jh = %s", [username])
        if cursor.fetchone():
            return 'Penjaga Hewan'
        
        cursor.execute("SELECT 1 FROM staf_admin WHERE username_sa = %s", [username])
        if cursor.fetchone():
            return 'Staf Administrasi'
    
    return ""

def view_habitat(request):
    if not (is_penjaga_hewan(request) or is_staff_admin(request)):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    if request.method == "POST" and "delete_nama" in request.POST:
        nama_to_delete = request.POST.get("delete_nama")
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM HABITAT WHERE nama = %s", [nama_to_delete])
        return redirect('habitat:view_habitat')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT nama, luas_area, kapasitas, status
            FROM HABITAT
            ORDER BY nama
        """)
        rows = cursor.fetchall()

    habitat_list = [
        {
            "nama": row[0],
            "luas": row[1],
            "kapasitas": row[2],
            "status": row[3],
        }
        for row in rows
    ]

    context = {
        "habitat_list": habitat_list,
        'user_role': get_user_role(request)
    }
    return render(request, 'view_habitat.html', context)

def create_habitat(request):
    if not (is_penjaga_hewan(request) or is_staff_admin(request)):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    if request.method == "POST":
        nama = request.POST['nama']
        luas = request.POST['luas']
        kapasitas = request.POST['kapasitas']
        status = request.POST['status']

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO HABITAT (nama, luas_area, kapasitas, status)
                VALUES (%s, %s, %s, %s)
            """, [nama, luas, kapasitas, status])
        
        return redirect('habitat:view_habitat')
    
    context = {
        'user_role': get_user_role(request)
    }

    return render(request, 'create_habitat.html', context)

def delete_habitat(request, nama):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM HABITAT WHERE nama = %s", [nama])
    return redirect('habitat:view_habitat')

def edit_habitat(request, nama):
    if not (is_penjaga_hewan(request) or is_staff_admin(request)):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    if request.method == "POST":
        luas = request.POST.get("luas")
        kapasitas = request.POST.get("kapasitas")
        status = request.POST.get("status")

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE HABITAT
                SET luas_area = %s, kapasitas = %s, status = %s
                WHERE nama = %s
            """, [luas, kapasitas, status, nama])

        return redirect('habitat:view_habitat')

    with connection.cursor() as cursor:
        cursor.execute("SELECT nama, luas_area, kapasitas, status FROM HABITAT WHERE nama = %s", [nama])
        row = cursor.fetchone()

    if not row:
        return render(request, '404.html', status=404)

    context = {
        "habitat": {
            "nama": row[0],
            "luas": row[1],
            "kapasitas": row[2],
            "status": row[3],
        },
        'user_role': get_user_role(request)
    }

    return render(request, 'edit_habitat.html', context)

def detail_habitat(request, nama):
    if not (is_penjaga_hewan(request) or is_staff_admin(request)):
        messages.error(request, 'Hanya dokter hewan yang dapat mengakses fitur ini.')
        return redirect('login')
    with connection.cursor() as cursor:
        cursor.execute("SELECT nama, luas_area, kapasitas, status FROM HABITAT WHERE nama = %s", [nama])
        h = cursor.fetchone()

        cursor.execute("""
            SELECT nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan
            FROM HEWAN WHERE nama_habitat = %s
        """, [nama])
        hewan_list = cursor.fetchall()

    context = {
        "habitat": {
            "nama": h[0],
            "luas": h[1],
            "kapasitas": h[2],
            "status": h[3]
        },
        "hewan_list": [
            {
                "nama": row[0],
                "spesies": row[1],
                "asal": row[2],
                "tanggal_lahir": row[3],
                "status": row[4]
            } for row in hewan_list
        ],
        'user_role': get_user_role(request)
    }
    return render(request, 'detail_habitat.html', context)
