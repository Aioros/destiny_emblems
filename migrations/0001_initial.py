# Generated by Django 2.0.3 on 2018-04-13 18:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Emblem',
            fields=[
                ('item_hash', models.BigIntegerField(primary_key=True, serialize=False)),
                ('index', models.IntegerField(null=True)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('tier', models.CharField(max_length=20)),
                ('icon', models.URLField()),
                ('secondary_icon', models.URLField()),
                ('main_emblem', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='destiny_emblems.Emblem')),
            ],
        ),
        migrations.CreateModel(
            name='Objective',
            fields=[
                ('item_hash', models.BigIntegerField(primary_key=True, serialize=False)),
                ('description', models.TextField()),
                ('progress_description', models.TextField()),
                ('main_emblem', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='destiny_emblems.Emblem')),
            ],
        ),
        migrations.AddField(
            model_name='emblem',
            name='main_objective',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='destiny_emblems.Objective'),
        ),
    ]
