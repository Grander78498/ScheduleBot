# Generated by Django 5.0.6 on 2024-08-06 11:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('queue_api', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='event',
            old_name='message',
            new_name='text',
        ),
        migrations.RemoveField(
            model_name='event',
            name='message_id',
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_id', models.BigIntegerField(null=True)),
                ('chat_id', models.BigIntegerField()),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='queue_api.event')),
            ],
        ),
    ]
