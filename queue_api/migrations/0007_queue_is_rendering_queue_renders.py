# Generated by Django 5.0.6 on 2024-07-29 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('queue_api', '0006_swaprequest_first_message_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='queue',
            name='is_rendering',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='queue',
            name='renders',
            field=models.BigIntegerField(default=0),
        ),
    ]
