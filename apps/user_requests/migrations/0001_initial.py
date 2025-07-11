# Generated by Django 5.2.3 on 2025-07-06 07:08

import django.core.validators
import django.db.models.deletion
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestCategory', fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('name', models.CharField(
                        help_text='Category name', max_length=100, unique=True)), ('description', models.TextField(
                            blank=True, help_text='Category description')), ('is_active', models.BooleanField(
                                default=True, help_text='Whether this category is active')), ('created_at', models.DateTimeField(
                                    auto_now_add=True)), ], options={
                'verbose_name_plural': 'Request Categories', 'ordering': ['name'], }, ), migrations.CreateModel(
            name='Request', fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('public_id', models.UUIDField(
                        default=uuid.uuid4, editable=False, help_text='Public identifier for this request', unique=True)), ('title', models.CharField(
                            help_text='Brief title describing what the buyer needs', max_length=200)), ('description', models.TextField(
                                help_text='Detailed description of the request')), ('budget', models.DecimalField(
                                    decimal_places=2, help_text='Maximum amount buyer is willing to pay', max_digits=10, validators=[
                                        django.core.validators.MinValueValidator(
                                            Decimal('0.01'))])), ('status', models.CharField(
                                                choices=[
                                                    ('open', 'Open'), ('accepted', 'Accepted'), ('delivered', 'Delivered'), ('completed', 'Completed'), ('disputed', 'Disputed'), ('cancelled', 'Cancelled')], default='open', help_text='Current status of the request', max_length=20)), ('deadline', models.DateTimeField(
                                                        blank=True, help_text='When the buyer needs this completed', null=True)), ('is_active', models.BooleanField(
                                                            default=True, help_text='Whether this request is active and visible')), ('is_deleted', models.BooleanField(
                                                                default=False, help_text='Soft delete flag')), ('created_at', models.DateTimeField(
                                                                    auto_now_add=True, help_text='When this request was created')), ('updated_at', models.DateTimeField(
                                                                        auto_now=True, help_text='When this request was last modified')), ('buyer', models.ForeignKey(
                                                                            help_text='User who created this request', on_delete=django.db.models.deletion.CASCADE, related_name='requests', to=settings.AUTH_USER_MODEL)), ('created_by', models.ForeignKey(
                                                                                help_text='User who created this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_requests', to=settings.AUTH_USER_MODEL)), ('updated_by', models.ForeignKey(
                                                                                    help_text='User who last updated this record', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_requests', to=settings.AUTH_USER_MODEL)), ('category', models.ForeignKey(
                                                                                        blank=True, help_text='Category of service requested', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='requests', to='user_requests.requestcategory')), ], options={
                'ordering': ['-created_at'], 'indexes': [
                    models.Index(
                        fields=[
                            'status', 'is_active', 'is_deleted'], name='user_reques_status_d611b3_idx'), models.Index(
                        fields=[
                            'buyer', 'status'], name='user_reques_buyer_i_8b95a9_idx'), models.Index(
                        fields=['created_at'], name='user_reques_created_3470fb_idx'), models.Index(
                        fields=['public_id'], name='user_reques_public__53c83b_idx'), models.Index(
                        fields=[
                            'category', 'is_active'], name='user_reques_categor_8a9893_idx')], }, ), ]
