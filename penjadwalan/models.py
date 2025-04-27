from django.db import models

class JadwalPenugasan(models.Model):
    username_lh = models.ForeignKey('accounts.PelatihHewan', models.DO_NOTHING, db_column='username_lh')
    tgl_penugasan = models.DateTimeField()
    nama_atraksi = models.ForeignKey('atraksi.Atraksi', models.DO_NOTHING, db_column='nama_atraksi', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'jadwal_penugasan'
        unique_together = (('username_lh', 'tgl_penugasan'),)