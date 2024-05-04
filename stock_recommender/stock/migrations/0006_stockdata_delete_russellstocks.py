# Generated by Django 5.0.1 on 2024-05-02 20:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock', '0005_dowstocks_nasdaqstocks_russellstocks'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockData',
            fields=[
                ('symbol', models.CharField(max_length=10, primary_key=True, serialize=False)),
                ('open', models.DecimalField(decimal_places=2, max_digits=10)),
                ('close', models.DecimalField(decimal_places=2, max_digits=10)),
                ('high', models.DecimalField(decimal_places=2, max_digits=10)),
                ('low', models.DecimalField(decimal_places=2, max_digits=10)),
                ('volume', models.BigIntegerField()),
                ('date', models.DateField()),
            ],
        ),
        migrations.DeleteModel(
            name='RUSSELLStocks',
        ),
    ]
