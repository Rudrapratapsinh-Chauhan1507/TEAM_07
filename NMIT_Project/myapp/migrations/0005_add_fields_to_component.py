from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0004_alter_billofmaterials_name_and_more'),  # <-- replace with your latest existing migration
    ]

    operations = [
        # Add ForeignKey to BillOfMaterials
        migrations.AddField(
            model_name='component',
            name='bom',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='myapp.billofmaterials'
            ),
        ),
        # Add quantity field
        migrations.AddField(
            model_name='component',
            name='quantity',
            field=models.FloatField(default=0),
        ),
        # Add available_quantity field
        migrations.AddField(
            model_name='component',
            name='available_quantity',
            field=models.FloatField(default=0),
        ),
    ]
