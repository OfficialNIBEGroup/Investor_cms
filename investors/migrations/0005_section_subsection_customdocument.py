# Generated manually for Section / SubSection / CustomDocument

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('investors', '0004_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('slug', models.SlugField(max_length=160, unique=True)),
                ('model_key', models.CharField(blank=True, default='', help_text='Internal key for system sections, e.g. annual_report', max_length=80)),
                ('description', models.TextField(blank=True, default='')),
                ('icon', models.CharField(blank=True, default='📁', max_length=20)),
                ('is_system', models.BooleanField(default=False, help_text='System sections cannot be deleted')),
                ('is_active', models.BooleanField(default=True, help_text='Inactive sections are hidden from upload / public')),
                ('show_on_public', models.BooleanField(default=True, help_text='Show this section on the public investors page')),
                ('allow_subsections', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SubSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150)),
                ('slug', models.SlugField(max_length=160)),
                ('is_active', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subsections', to='investors.section')),
            ],
            options={
                'ordering': ['display_order', 'name'],
                'unique_together': {('section', 'slug')},
            },
        ),
        migrations.CreateModel(
            name='CustomDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='investor_documents/custom/')),
                ('external_url', models.URLField(blank=True, null=True)),
                ('published', models.BooleanField(default=True)),
                ('display_order', models.PositiveIntegerField(default=0)),
                ('extra_info', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='custom_documents', to='investors.section')),
                ('subsection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='investors.subsection')),
            ],
            options={
                'ordering': ['-display_order', '-created_at'],
            },
        ),
    ]
