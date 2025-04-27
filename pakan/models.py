from django.db import models

class Pakan(models.Model):
    id_hewan = models.ForeignKey('satwa.Hewan', models.DO_NOTHING, db_column='id_hewan')
    jadwal = models.DateTimeField()
    jenis = models.CharField(max_length=50)
    jumlah = models.IntegerField()
    status = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'pakan'
        unique_together = (('id_hewan', 'jadwal'),)

class Memberi(models.Model):
    id_hewan = models.OneToOneField('satwa.Hewan', models.DO_NOTHING, db_column='id_hewan', primary_key=True)
    jadwal = models.DateTimeField()
    username_jh = models.ForeignKey('accounts.Pengguna', models.DO_NOTHING, db_column='username_jh', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'memberi'
