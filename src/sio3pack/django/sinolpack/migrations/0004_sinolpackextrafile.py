# Generated by Django 4.2.21 on 2025-05-18 11:13

from django.db import migrations, models
import django.db.models.deletion
import sio3pack.django.common.models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0006_alter_sio3packmainmodelsolution_package_and_more"),
        ("sinolpack", "0003_sinolpackspecialfile"),
    ]

    operations = [
        migrations.CreateModel(
            name="SinolpackExtraFile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("package_path", models.CharField(max_length=255, verbose_name="package path")),
                (
                    "file",
                    models.FileField(
                        upload_to=sio3pack.django.common.models.make_problem_filename, verbose_name="file"
                    ),
                ),
                (
                    "package",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="extra_files", to="common.sio3package"
                    ),
                ),
            ],
        ),
    ]
