from django.db import migrations

def drop_column_if_exists(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE orders_order DROP COLUMN IF EXISTS is_archived;")

def reverse_drop_column(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE orders_order ADD COLUMN is_archived boolean NOT NULL DEFAULT false;")

class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0004_alter_order_status"),
    ]

    operations = [
        migrations.RunPython(drop_column_if_exists, reverse_drop_column),
    ]
