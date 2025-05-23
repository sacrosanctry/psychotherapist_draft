# Generated by Django 5.2.1 on 2025-05-16 04:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0002_criterion_score_meaning_1_criterion_score_meaning_9'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MatchingResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.FloatField()),
                ('rank', models.IntegerField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matching_results', to=settings.AUTH_USER_MODEL)),
                ('therapist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='client_matches', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['client', 'rank'],
                'unique_together': {('client', 'therapist')},
            },
        ),
    ]
