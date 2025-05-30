# Generated by Django 5.2 on 2025-04-27 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Hewan',
            fields=[
                ('id', models.UUIDField(primary_key=True, serialize=False)),
                ('nama', models.CharField(blank=True, max_length=100, null=True)),
                ('spesies', models.CharField(max_length=100)),
                ('asal_hewan', models.CharField(max_length=100)),
                ('tanggal_lahir', models.DateField(blank=True, null=True)),
                ('status_kesehatan', models.CharField(max_length=50)),
                ('url_foto', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'hewan',
                'managed': False,
            },
        ),
    ]
