import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directory', '0003_wastebank_latitude_wastebank_longitude'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wastebank',
            name='latitude',
            field=models.DecimalField(decimal_places=6, default=-6.205323, max_digits=9, validators=[django.core.validators.MinValueValidator(-90), django.core.validators.MaxValueValidator(90)]),
        ),
        migrations.AlterField(
            model_name='wastebank',
            name='longitude',
            field=models.DecimalField(decimal_places=6, default=106.847208, max_digits=9, validators=[django.core.validators.MinValueValidator(-180), django.core.validators.MaxValueValidator(180)]),
        ),
    ]
