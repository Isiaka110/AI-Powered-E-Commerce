from django.db import migrations


def add_missing_whatsapp_columns(apps, schema_editor):
    StoreSettings = apps.get_model('store', 'StoreSettings')
    table_name = StoreSettings._meta.db_table

    with schema_editor.connection.cursor() as cursor:
        existing_columns = {
            column.name for column in schema_editor.connection.introspection.get_table_description(cursor, table_name)
        }

    for field_name in (
        'owner_whatsapp_number',
        'whatsapp_message_template',
        'auto_open_whatsapp_on_checkout',
    ):
        if field_name in existing_columns:
            continue
        field = StoreSettings._meta.get_field(field_name)
        schema_editor.add_field(StoreSettings, field)


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0011_storesettings_whatsapp_checkout'),
    ]

    operations = [
        migrations.RunPython(add_missing_whatsapp_columns, migrations.RunPython.noop),
    ]
