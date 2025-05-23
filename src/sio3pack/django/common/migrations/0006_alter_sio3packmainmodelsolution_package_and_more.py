# Generated by Django 4.2.20 on 2025-05-08 13:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0005_alter_sio3packtest_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sio3packmainmodelsolution",
            name="package",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name="main_model_solution", to="common.sio3package"
            ),
        ),
        migrations.AlterField(
            model_name="sio3packnametranslation",
            name="language",
            field=models.CharField(
                choices=[("en", "English"), ("pl", "Polski")], max_length=7, verbose_name="language code"
            ),
        ),
        migrations.AlterField(
            model_name="sio3packstatement",
            name="language",
            field=models.CharField(
                blank=True,
                choices=[("en", "English"), ("pl", "Polski")],
                max_length=7,
                null=True,
                verbose_name="language code",
            ),
        ),
    ]
