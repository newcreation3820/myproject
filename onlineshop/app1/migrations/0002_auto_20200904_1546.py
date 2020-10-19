# Generated by Django 3.1 on 2020-09-04 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fname', models.CharField(max_length=100)),
                ('lname', models.CharField(max_length=100)),
                ('email', models.CharField(max_length=100)),
                ('mobile', models.CharField(max_length=100)),
                ('address', models.TextField()),
                ('password', models.CharField(max_length=100)),
                ('cpassword', models.CharField(max_length=100)),
            ],
        ),
        migrations.AlterField(
            model_name='contact',
            name='feedback',
            field=models.TextField(),
        ),
    ]
