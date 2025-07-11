# Generated by Django 5.2.3 on 2025-07-08 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_requests', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='request',
            name='status',
            field=models.CharField(
                choices=[
                    ('open',
                     'Open'),
                    ('accepted',
                     'Accepted'),
                    ('delivered',
                     'Delivered'),
                    ('completed',
                     'Completed'),
                    ('disputed',
                     'Disputed'),
                    ('pending_escrow',
                     'Pending Escrow'),
                    ('cancelled',
                     'Cancelled')],
                default='open',
                help_text='Current status of the request',
                max_length=20),
        ),
    ]
