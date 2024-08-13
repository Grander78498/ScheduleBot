# Generated by Django 5.0.6 on 2024-08-13 16:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('queue_api', '0005_student_studentgroup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='group_member',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='queue_api.groupmember'),
        ),
        migrations.AlterField(
            model_name='studentgroup',
            name='group',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='queue_api.telegramgroup'),
        ),
    ]
