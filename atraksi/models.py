# ============================
# atraksi/models.py
# ============================
from django.db import models

class Fasilitas(models.Model):
    nama = models.CharField(primary_key=True, max_length=50)
    jadwal = models.DateTimeField()
    kapasitas_max = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'fasilitas'

class Atraksi(models.Model):
    nama_atraksi = models.OneToOneField('atraksi.Fasilitas', models.DO_NOTHING, db_column='nama_atraksi', primary_key=True)
    lokasi = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'atraksi'

class Wahana(models.Model):
    nama_wahana = models.OneToOneField('atraksi.Fasilitas', models.DO_NOTHING, db_column='nama_wahana', primary_key=True)
    peraturan = models.TextField()

    class Meta:
        managed = False
        db_table = 'wahana'

class Berpartisipasi(models.Model):
    nama_fasilitas = models.ForeignKey('atraksi.Fasilitas', models.DO_NOTHING, db_column='nama_fasilitas', primary_key=True)
    id_hewan = models.ForeignKey('satwa.Hewan', models.DO_NOTHING, db_column='id_hewan')

    class Meta:
        managed = False
        db_table = 'berpartisipasi'
        unique_together = (('nama_fasilitas', 'id_hewan'),)
        constraints = [
            models.UniqueConstraint(fields=['nama_fasilitas', 'id_hewan'], name='berpartisipasi_pk')
        ]
