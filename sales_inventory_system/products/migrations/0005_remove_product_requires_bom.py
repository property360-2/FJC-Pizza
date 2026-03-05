from django.db import migrations

def drop_column_if_exists(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE products_product DROP COLUMN IF EXISTS requires_bom;")

def reverse_drop_column(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE products_product ADD COLUMN requires_bom boolean NOT NULL DEFAULT false;")

class Migration(migrations.Migration):

    dependencies = [
        ("products", "0004_ingredient_is_available_alter_ingredient_unit"),
    ]

    operations = [
        migrations.RunPython(drop_column_if_exists, reverse_drop_column),
    ]
