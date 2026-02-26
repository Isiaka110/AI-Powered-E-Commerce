from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_promocode_sitebanner'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_name', models.CharField(max_length=120)),
                ('contact_phone', models.CharField(max_length=30)),
                ('storefront_slug', models.SlugField(blank=True, max_length=140, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='vendor_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
