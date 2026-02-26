from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0009_vendorprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='fulfillment_method',
            field=models.CharField(choices=[('PICKUP', 'Pickup'), ('WAYBILL', 'Waybill delivery')], default='PICKUP', max_length=10),
        ),
        migrations.AddField(
            model_name='cart',
            name='logistics_note',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='order',
            name='fulfillment_method',
            field=models.CharField(choices=[('PICKUP', 'Pickup'), ('WAYBILL', 'Waybill delivery')], default='PICKUP', max_length=10),
        ),
        migrations.AddField(
            model_name='order',
            name='logistics_note',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='order',
            name='pre_purchase_instruction_snapshot',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='order',
            name='receipt_channel_used',
            field=models.CharField(default='EMAIL', max_length=20),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='allow_pickup',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='allow_waybill_delivery',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='pre_purchase_instruction',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='receipt_channel',
            field=models.CharField(choices=[('EMAIL', 'Email receipt'), ('DM', 'Send receipt to direct message'), ('SOCIAL_INBOX', 'Send receipt to social inbox'), ('NONE', 'Do not send a receipt automatically')], default='EMAIL', max_length=20),
        ),
    ]
