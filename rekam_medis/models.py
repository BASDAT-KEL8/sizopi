from django.db import models

class CatatanMedis(models.Model):
    id_hewan = models.ForeignKey('satwa.Hewan', models.DO_NOTHING, db_column='id_hewan')
    username_dh = models.ForeignKey('accounts.Pengguna', models.DO_NOTHING, db_column='username_dh', blank=True, null=True)
    tanggal_pemeriksaan = models.DateField()
    diagnosis = models.CharField(max_length=100, blank=True, null=True)
    pengobatan = models.CharField(max_length=100, blank=True, null=True)
    status_kesehatan = models.CharField(max_length=50)
    catatan_tindak_lanjut = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'catatan_medis'
        unique_together = (('id_hewan', 'tanggal_pemeriksaan'),)

class JadwalPemeriksaanKesehatan(models.Model):
    id_hewan = models.ForeignKey('satwa.Hewan', models.DO_NOTHING, db_column='id_hewan')
    tgl_pemeriksaan_selanjutnya = models.DateField()
    freq_pemeriksaan_rutin = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'jadwal_pemeriksaan_kesehatan'
        unique_together = (('id_hewan', 'tgl_pemeriksaan_selanjutnya'),)