# Generated by Django 4.2.3 on 2025-04-26 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_alter_customerrequest_request_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='ingredients',
            field=models.TextField(blank=True),
        ),
    ]
