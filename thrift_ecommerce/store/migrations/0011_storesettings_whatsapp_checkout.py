from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0010_owner_studio_checkout_controls'),
    ]

    operations = [
        migrations.AddField(
            model_name='storesettings',
            name='auto_open_whatsapp_on_checkout',
            field=models.BooleanField(default=True, help_text='Automatically open WhatsApp with order details after successful checkout.'),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='owner_whatsapp_number',
            field=models.CharField(blank=True, help_text='Use international format, e.g. 2348012345678 (no + or spaces).', max_length=20),
        ),
        migrations.AddField(
            model_name='storesettings',
            name='whatsapp_message_template',
            field=models.TextField(blank=True, default='Hi {{store_name}}, I just completed order #{{order_id}} for ₦{{total_paid}}.', help_text='Template supports: {{store_name}}, {{order_id}}, {{total_paid}}, {{fulfillment_method}}, {{logistics_note}}, {{item_summary}}'),
        ),
    ]
