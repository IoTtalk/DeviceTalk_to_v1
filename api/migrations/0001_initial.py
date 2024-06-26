# Generated by Django 3.2.6 on 2022-07-30 18:43

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BasicFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('dir_path', models.CharField(default='/', max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('global_var_setup', models.TextField(default='')),
                ('gvs_readonly_lines', models.JSONField(default=list)),
                ('dm_name', models.CharField(max_length=100, verbose_name='Device Model Name')),
                ('server_url', models.CharField(max_length=255)),
                ('device_address', models.CharField(default='', max_length=50)),
                ('push_interval', models.FloatField()),
                ('basic_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.basicfile')),
            ],
        ),
        migrations.CreateModel(
            name='DeviceDf',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='df_set', to='api.device')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DeviceLibrary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('global_var_setup', models.TextField(default='')),
                ('gvs_readonly_lines', models.JSONField(default=list)),
                ('dir_path', models.CharField(default='/', max_length=255)),
                ('basic_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.basicfile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DeviceLibraryDf',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('device_library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='df_set', to='api.devicelibrary')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DfType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('df_type', models.CharField(choices=[('idf', 'idf'), ('odf', 'odf')], max_length=10, verbose_name='Type')),
                ('params', models.JSONField(default=list, verbose_name='Parameters')),
            ],
            options={
                'verbose_name': 'DfType',
            },
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('dir_path', models.CharField(default='/', max_length=255)),
                ('global_var_setup', models.TextField(default='')),
                ('gvs_readonly_lines', models.JSONField(default=list)),
                ('basic_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.basicfile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LibraryFunction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('var_define', models.TextField(blank=True)),
                ('import_string', models.TextField(blank=True)),
                ('member_var_define', models.TextField(blank=True)),
                ('init_content', models.TextField(blank=True)),
                ('runs_content', models.TextField(blank=True)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.library')),
            ],
        ),
        migrations.CreateModel(
            name='SaFunction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('var_setup', models.TextField(blank=True)),
                ('code', models.TextField()),
                ('readonly_lines', models.JSONField(default=list)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('function_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.dftype')),
                ('library_ref', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.libraryfunction')),
            ],
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
            options={
                'unique_together': {('name',)},
            },
        ),
        migrations.CreateModel(
            name='DeviceLibraryDfHasSaFunction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('var_setup', models.TextField(blank=True)),
                ('selected', models.BooleanField(default=False)),
                ('device_library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='function_relation_set', to='api.devicelibrarydf')),
                ('function', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.safunction')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='devicelibrarydf',
            name='df_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.dftype'),
        ),
        migrations.AddField(
            model_name='devicelibrarydf',
            name='functions',
            field=models.ManyToManyField(blank=True, through='api.DeviceLibraryDfHasSaFunction', to='api.SaFunction'),
        ),
        migrations.AddField(
            model_name='devicelibrary',
            name='dependency_library',
            field=models.ManyToManyField(blank=True, to='api.Library'),
        ),
        migrations.AddField(
            model_name='devicelibrary',
            name='functions',
            field=models.ManyToManyField(blank=True, to='api.SaFunction'),
        ),
        migrations.AddField(
            model_name='devicelibrary',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='DeviceHasLibrary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.BigIntegerField()),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='library_set', to='api.device')),
                ('device_library', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.devicelibrary')),
                ('library', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.library')),
            ],
            options={
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='DeviceDfHasSaFunction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('var_setup', models.TextField(blank=True)),
                ('selected', models.BooleanField(default=False)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='function_relation_set', to='api.devicedf')),
                ('function', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.safunction')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='devicedf',
            name='df_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.dftype'),
        ),
        migrations.AddField(
            model_name='devicedf',
            name='functions',
            field=models.ManyToManyField(blank=True, through='api.DeviceDfHasSaFunction', to='api.SaFunction'),
        ),
        migrations.AddField(
            model_name='device',
            name='functions',
            field=models.ManyToManyField(blank=True, to='api.SaFunction'),
        ),
        migrations.AddField(
            model_name='device',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='basicfile',
            name='language',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.language'),
        ),
        migrations.AlterUniqueTogether(
            name='device',
            unique_together={('name', 'dm_name', 'user')},
        ),
        migrations.AlterUniqueTogether(
            name='basicfile',
            unique_together={('name', 'language')},
        ),
    ]
