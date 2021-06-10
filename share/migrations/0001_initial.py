# Generated by Django 3.2.4 on 2021-06-10 20:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organization",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("hospital", "醫院"),
                            ("fire_department", "消防局"),
                            ("police_station", "警局"),
                            ("other", "其他"),
                        ],
                        max_length=16,
                    ),
                ),
                ("type_other", models.CharField(max_length=20)),
                ("name", models.CharField(max_length=32)),
                (
                    "city",
                    models.CharField(
                        choices=[
                            ("KLU", "基隆市"),
                            ("TPH", "新北市"),
                            ("TPE", "台北市"),
                            ("TYC", "桃園市"),
                            ("HSH", "新竹縣"),
                            ("HSC", "新竹市"),
                            ("MAL", "苗栗縣"),
                            ("TXG", "台中市"),
                            ("CWH", "彰化縣"),
                            ("NTO", "南投縣"),
                            ("YLH", "雲林縣"),
                            ("CHY", "嘉義縣"),
                            ("CYI", "嘉義市"),
                            ("TNN", "台南市"),
                            ("KHH", "高雄市"),
                            ("LNN", "連江縣"),
                            ("ILN", "宜蘭縣"),
                            ("PEH", "澎湖縣"),
                            ("KMN", "金門縣"),
                            ("IUH", "屏東縣"),
                            ("TTT", "台東縣"),
                            ("HWA", "花蓮縣"),
                        ],
                        max_length=16,
                    ),
                ),
                ("address", models.CharField(max_length=128)),
                ("phone", models.CharField(max_length=15)),
                ("office_hours", models.CharField(max_length=128)),
                (
                    "other_contact_method",
                    models.CharField(
                        choices=[
                            ("_not_set_", "未設定"),
                            ("line", "Line"),
                            ("fb", "FB"),
                            ("email", "Email"),
                        ],
                        max_length=16,
                    ),
                ),
                ("other_contact", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RequiredItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                ("amount", models.PositiveSmallIntegerField()),
                (
                    "unit",
                    models.CharField(
                        choices=[("piece", "個"), ("set", "套")], max_length=16
                    ),
                ),
                ("ended_date", models.DateField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="share.organization",
                    ),
                ),
            ],
            options={
                "ordering": ["-ended_date"],
            },
        ),
        migrations.CreateModel(
            name="Donator",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("phone", models.CharField(max_length=15)),
                (
                    "other_contact_method",
                    models.CharField(
                        choices=[
                            ("_not_set_", "未設定"),
                            ("line", "Line"),
                            ("fb", "FB"),
                            ("email", "Email"),
                        ],
                        max_length=16,
                    ),
                ),
                ("other_contact", models.CharField(max_length=128)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
