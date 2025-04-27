from django.db import models



class Hewan(models.Model):
    id = models.UUIDField(primary_key=True)
    nama = models.CharField(max_length=100, blank=True, null=True)
    spesies = models.CharField(max_length=100)
    asal_hewan = models.CharField(max_length=100)
    tanggal_lahir = models.DateField(blank=True, null=True)
    status_kesehatan = models.CharField(max_length=50)
    nama_habitat = models.ForeignKey('habitat.Habitat', models.DO_NOTHING, db_column='nama_habitat', blank=True, null=True)
    url_foto = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'hewan'