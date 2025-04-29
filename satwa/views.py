import uuid
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect, render


def view_satwa(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat
            FROM HEWAN
            ORDER BY nama
        """)
        rows = cursor.fetchall()

    satwa_list = [
        {
            "id": row[0],  # ← required for edit/delete URL
            "nama": row[1],
            "spesies": row[2],
            "asal": row[3],
            "tanggal_lahir": row[4],
            "status": row[5],
            "habitat": row[6],
        }
        for row in rows
    ]

    context = {
        "satwa_list": satwa_list
    }
    return render(request, 'view_satwa.html', context)

def delete_satwa(request, id):
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM HEWAN WHERE id = %s", [id])
    return redirect('satwa:view_satwa')


def create_satwa(request):
    if request.method == "POST":
        nama = request.POST.get("nama")
        spesies = request.POST.get("spesies")
        asal = request.POST.get("asal")
        tanggal = request.POST.get("tanggal_lahir") or None
        status = request.POST.get("status")
        habitat = request.POST.get("habitat")
        url_foto = request.POST.get("foto")
        id_baru = str(uuid.uuid4())

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO HEWAN (id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, [id_baru, nama, spesies, asal, tanggal, status, habitat, url_foto])
        
        return redirect('satwa:view_satwa')

    with connection.cursor() as cursor:
        cursor.execute("SELECT nama FROM HABITAT ORDER BY nama")
        habitat_options = [row[0] for row in cursor.fetchall()]

    return render(request, 'create_satwa.html', {
        "habitat_options": habitat_options
    })

def delete_satwa(request, id):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM HEWAN WHERE id = %s", [id])
    return redirect('satwa:view_satwa')

def edit_satwa(request, id):
    if request.method == "POST":
        nama = request.POST.get("nama")
        spesies = request.POST.get("spesies")
        asal = request.POST.get("asal")
        tanggal = request.POST.get("tanggal_lahir") or None
        status = request.POST.get("status")
        habitat = request.POST.get("habitat")
        foto = request.POST.get("foto")

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE HEWAN
                SET nama = %s, spesies = %s, asal_hewan = %s, tanggal_lahir = %s,
                    status_kesehatan = %s, nama_habitat = %s, url_foto = %s
                WHERE id = %s
            """, [nama, spesies, asal, tanggal, status, habitat, foto, id])

        return redirect('satwa:view_satwa')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, nama, spesies, asal_hewan, tanggal_lahir, status_kesehatan, nama_habitat, url_foto
            FROM HEWAN WHERE id = %s
        """, [id])
        data = cursor.fetchone()

        cursor.execute("SELECT nama FROM HABITAT ORDER BY nama")
        habitat_options = [row[0] for row in cursor.fetchall()]

    context = {
        "satwa": {
            "id": data[0],
            "nama": data[1],
            "spesies": data[2],
            "asal": data[3],
            "tanggal_lahir": data[4],
            "status": data[5],
            "habitat": data[6],
            "foto": data[7]
        },
        "habitat_options": habitat_options
    }

    return render(request, 'edit_satwa.html', context)
