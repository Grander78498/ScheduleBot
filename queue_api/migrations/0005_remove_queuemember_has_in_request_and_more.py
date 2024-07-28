# Generated by Django 5.0.6 on 2024-07-28 12:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('queue_api', '0004_queuemember_has_in_request_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='queuemember',
            name='has_in_request',
        ),
        migrations.RemoveField(
            model_name='queuemember',
            name='has_out_request',
        ),
        migrations.CreateModel(
            name='SwapRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='first_member', to='queue_api.queuemember')),
                ('second_member', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='second_member', to='queue_api.queuemember')),
            ],
        ),
    ]
