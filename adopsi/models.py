from django.db import models
from django.contrib.auth.models import User
import uuid
import datetime

# Proxy model untuk tabel HEWAN dari modul satwa
class Hewan(models.Model):
    """
    Model proxy untuk tabel HEWAN dari modul satwa
    """
    class Meta:
        managed = False
        db_table = 'HEWAN'

# Proxy model untuk tabel PENGUNJUNG dari modul accounts
class Pengunjung(models.Model):
    """
    Model proxy untuk tabel PENGUNJUNG dari modul accounts
    """
    class Meta:
        managed = False
        db_table = 'PENGUNJUNG'

class Adopter(models.Model):
    username_adopter = models.OneToOneField('accounts.Pengunjung', models.DO_NOTHING, db_column='username_adopter', blank=True, null=True)
    id_adopter = models.UUIDField(primary_key=True)
    total_kontribusi = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'adopter'

class Adopsi(models.Model):
    id_adopter = models.ForeignKey('adopsi.Adopter', models.DO_NOTHING, db_column='id_adopter')
    id_hewan = models.ForeignKey('satwa.Hewan', models.DO_NOTHING, db_column='id_hewan')
    status_pembayaran = models.CharField(max_length=10)
    tgl_mulai_adopsi = models.DateField()
    tgl_berhenti_adopsi = models.DateField()
    kontribusi_finansial = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'adopsi'
        unique_together = (('id_adopter', 'id_hewan', 'tgl_mulai_adopsi'),)

class Individu(models.Model):
    nik = models.CharField(primary_key=True, max_length=16)
    nama = models.CharField(max_length=100)
    id_adopter = models.ForeignKey('adopsi.Adopter', models.DO_NOTHING, db_column='id_adopter', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'individu'

class Organisasi(models.Model):
    npp = models.CharField(primary_key=True, max_length=8)
    nama_organisasi = models.CharField(max_length=100)
    id_adopter = models.ForeignKey('adopsi.Adopter', models.DO_NOTHING, db_column='id_adopter', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'organisasi'