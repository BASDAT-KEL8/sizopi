# Generated by Django 5.2 on 2025-04-27 12:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Fasilitas',
            fields=[
                ('nama', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('jadwal', models.DateTimeField()),
                ('kapasitas_max', models.IntegerField()),
            ],
            options={
                'db_table': 'fasilitas',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Berpartisipasi',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'db_table': 'berpartisipasi',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Atraksi',
            fields=[
                ('nama_atraksi', models.OneToOneField(db_column='nama_atraksi', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='atraksi.fasilitas')),
                ('lokasi', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'atraksi',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Wahana',
            fields=[
                ('nama_wahana', models.OneToOneField(db_column='nama_wahana', on_delete=django.db.models.deletion.DO_NOTHING, primary_key=True, serialize=False, to='atraksi.fasilitas')),
                ('peraturan', models.TextField()),
            ],
            options={
                'db_table': 'wahana',
                'managed': False,
            },
        ),
    ]
