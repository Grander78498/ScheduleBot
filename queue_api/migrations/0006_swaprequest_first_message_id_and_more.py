# Generated by Django 5.0.6 on 2024-07-28 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('queue_api', '0005_remove_queuemember_has_in_request_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='swaprequest',
            name='first_message_id',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='swaprequest',
            name='second_message_id',
            field=models.BigIntegerField(null=True),
        ),
    ]