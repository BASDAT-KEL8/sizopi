from django.db import connection

def role_context(request):
    user_role = 'guest'
    username = request.session.get('username')

    if username:
        with connection.cursor() as cursor:
            # Cek role berurutan
            cursor.execute("SELECT 1 FROM sizopi.dokter_hewan WHERE username_dh = %s", [username])
            if cursor.fetchone():
                user_role = 'Dokter Hewan'
            else:
                cursor.execute("SELECT 1 FROM sizopi.penjaga_hewan WHERE username_jh = %s", [username])
                if cursor.fetchone():
                    user_role = 'Penjaga Hewan'
                else:
                    cursor.execute("SELECT 1 FROM sizopi.pelatih_hewan WHERE username_lh = %s", [username])
                    if cursor.fetchone():
                        user_role = 'Staf Pelatih Pertunjukan'
                    else:
                        cursor.execute("SELECT 1 FROM sizopi.staf_admin WHERE username_sa = %s", [username])
                        if cursor.fetchone():
                            user_role = 'Staf Administrasi'
                        else:
                            cursor.execute("SELECT 1 FROM sizopi.pengunjung WHERE username_p = %s", [username])
                            if cursor.fetchone():
                                cursor.execute("""
                                    SELECT 1 FROM sizopi.adopter 
                                    WHERE username_adopter = %s
                                """, [username])
                                if cursor.fetchone():
                                    user_role = 'pengunjung_adopter'
                                else:
                                    user_role = 'Pengunjung'

    return {'user_role': user_role}
