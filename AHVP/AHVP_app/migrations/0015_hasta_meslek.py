# Generated by Django 5.1.2 on 2024-11-09 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('AHVP_app', '0014_muayene_beck_anksiyete_muayene_beck_depresyon_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='hasta',
            name='meslek',
            field=models.CharField(default='bilinmiyor', max_length=100),
            preserve_default=False,
        ),
    ]
