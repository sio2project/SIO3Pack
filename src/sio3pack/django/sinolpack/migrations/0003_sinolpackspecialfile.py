# Generated by Django 4.2.20 on 2025-05-05 09:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0004_sio3packtest_sio3packmainmodelsolution"),
        ("sinolpack", "0002_alter_sinolpackadditionalfile_package_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SinolpackSpecialFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(max_length=30, verbose_name="type")),
                (
                    "additional_file",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="special_file",
                        to="sinolpack.sinolpackadditionalfile",
                    ),
                ),
                (
                    "package",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="special_files",
                        to="common.sio3package",
                    ),
                ),
            ],
            options={
                "verbose_name": "special file",
                "verbose_name_plural": "special files",
            },
        ),
    ]
