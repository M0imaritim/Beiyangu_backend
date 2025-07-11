# Generated by Django 5.2.3 on 2025-07-10 05:48

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bids', '0002_alter_bid_created_by_alter_bid_updated_by'),
        ('escrow', '0002_alter_escrowtransaction_options_and_more'),
        ('user_requests', '0002_alter_request_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='escrowtransaction',
            name='bid',
            field=models.OneToOneField(
                blank=True,
                help_text='The accepted bid this escrow is for',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='escrow',
                to='bids.bid'),
        ),
        migrations.AddField(
            model_name='escrowtransaction',
            name='expires_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When escrow expires if not completed',
                null=True),
        ),
        migrations.AddField(
            model_name='escrowtransaction',
            name='payment_token',
            field=models.CharField(
                blank=True,
                help_text='Simulated payment token',
                max_length=100),
        ),
        migrations.AlterField(
            model_name='escrowtransaction',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('credit_card',
                     'Credit Card'),
                    ('debit_card',
                     'Debit Card'),
                    ('bank_transfer',
                     'Bank Transfer'),
                    ('paypal',
                     'PayPal'),
                    ('apple_pay',
                     'Apple Pay'),
                    ('google_pay',
                     'Google Pay'),
                    ('stripe',
                     'Stripe')],
                default='credit_card',
                help_text='Payment method used for escrow',
                max_length=50),
        ),
        migrations.AlterField(
            model_name='escrowtransaction',
            name='payment_reference',
            field=models.CharField(
                blank=True,
                help_text='Simulated payment reference',
                max_length=100),
        ),
        migrations.AlterField(
            model_name='escrowtransaction',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending',
                     'Pending Setup'),
                    ('locked',
                     'Locked'),
                    ('released',
                     'Released'),
                    ('held',
                     'Held for Dispute'),
                    ('refunded',
                     'Refunded'),
                    ('failed',
                     'Failed')],
                default='pending',
                help_text='Current status of the escrow',
                max_length=20),
        ),
        migrations.AddIndex(
            model_name='escrowtransaction',
            index=models.Index(
                fields=['payment_method'],
                name='escrow_escr_payment_06b033_idx'),
        ),
    ]
