# Generated by Django 2.1 on 2018-08-15 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(max_length=500, primary_key=True, serialize=False)),
                ('spotify_access_token', models.CharField(max_length=500)),
                ('spotify_refresh_token', models.CharField(max_length=500)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
