from django.db import models

class Pengguna(models.Model):
    username = models.CharField(primary_key=True, max_length=50)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=50)
    nama_depan = models.CharField(max_length=50)
    nama_tengah = models.CharField(max_length=50, blank=True, null=True)
    nama_belakang = models.CharField(max_length=50)
    no_telepon = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'pengguna'

class Pengunjung(models.Model):
    username_p = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_p', primary_key=True)
    alamat = models.CharField(max_length=200)
    tgl_lahir = models.DateField()

    class Meta:
        managed = False
        db_table = 'pengunjung'

class DokterHewan(models.Model):
    username_dh = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_dh', primary_key=True)
    no_str = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'dokter_hewan'

class PelatihHewan(models.Model):
    username_lh = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_lh', primary_key=True)
    id_staf = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'pelatih_hewan'

class PenjagaHewan(models.Model):
    username_jh = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_jh', primary_key=True)
    id_staf = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'penjaga_hewan'

class StafAdmin(models.Model):
    username_sa = models.OneToOneField(Pengguna, models.DO_NOTHING, db_column='username_sa', primary_key=True)
    id_staf = models.UUIDField()

    class Meta:
        managed = False
        db_table = 'staf_admin'

class Spesialisasi(models.Model):
    pk = models.CompositePrimaryKey('username_sh', 'nama_spesialisasi')
    username_sh = models.ForeignKey(DokterHewan, models.DO_NOTHING, db_column='username_sh')
    nama_spesialisasi = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'spesialisasi'
        unique_together = (('username_sh', 'nama_spesialisasi'),)