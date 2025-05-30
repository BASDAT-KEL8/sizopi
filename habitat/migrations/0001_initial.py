# Generated by Django 5.2 on 2025-04-27 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Habitat',
            fields=[
                ('nama', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('luas_area', models.DecimalField(decimal_places=2, max_digits=10)),
                ('kapasitas', models.IntegerField()),
                ('status', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'habitat',
                'managed': False,
            },
        ),
    ]
