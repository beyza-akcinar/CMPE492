# Generated by Django 4.2.16 on 2024-12-19 22:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("AHVP_app", "0003_alter_hasta_hasta_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="muayene",
            old_name="ravlt_forgetting",
            new_name="RAVLT_forgetting",
        ),
    ]
