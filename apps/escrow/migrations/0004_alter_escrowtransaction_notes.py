# Generated by Django 5.2.3 on 2025-07-10 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('escrow', '0003_escrowtransaction_bid_escrowtransaction_expires_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='escrowtransaction',
            name='notes',
            field=models.TextField(blank=True, help_text='Additional notes about this escrow transaction'),
        ),
    ]
