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
            name="Session",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                ("image_url", models.URLField(blank=True, default="")),
                ("date", models.DateTimeField()),
                ("duration_minutes", models.PositiveIntegerField(default=60)),
                ("max_seats", models.PositiveIntegerField(default=20)),
                ("price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("cancelled", "Cancelled")], default="published", max_length=12)),
                ("tags", models.CharField(blank=True, default="", max_length=500)),
                ("location", models.CharField(blank=True, default="Online", max_length=300)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("creator", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-date"],
            },
        ),
    ]
