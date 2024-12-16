# Generated by Django 5.0.6 on 2024-12-16 12:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('queue_api', '0008_alter_student_rating_alter_student_scholarship'),
    ]

    operations = [
        migrations.CreateModel(
            name='Santa',
            fields=[
                ('event_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='queue_api.event')),
                ('is_active', models.BooleanField(default=True)),
            ],
            bases=('queue_api.event',),
        ),
        migrations.CreateModel(
            name='SantaMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('santa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='queue_api.santa')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='queue_api.telegramuser')),
            ],
        ),
    ]