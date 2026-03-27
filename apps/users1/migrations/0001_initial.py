from django.db import migrations, models
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('email', models.EmailField(blank=True, max_length=254, null=True, unique=True)),
                ('phone_number', models.CharField(
                    blank=True, max_length=15, null=True, unique=True,
                    validators=[django.core.validators.RegexValidator(
                        message="Telefon raqam to'g'ri formatda bo'lishi kerak. Masalan: +998901234567",
                        regex='^\\+\\d{10,15}$'
                    )]
                )),
                ('user_type', models.CharField(
                    blank=True,
                    choices=[('candidate', 'Nomzod'), ('organization', 'Tashkilot')],
                    max_length=20, null=True
                )),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('middle_name', models.CharField(blank=True, max_length=150, verbose_name='Sharif')),
                ('organization_name', models.CharField(blank=True, max_length=255, null=True)),
                ('position', models.CharField(blank=True, max_length=150, null=True, verbose_name='Lavozim')),
                ('chat_id', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='users1_user_set', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='users1_user_set', to='auth.permission')),
            ],
            options={
                'verbose_name': 'Foydalanuvchi',
                'verbose_name_plural': 'Foydalanuvchilar',
            },
        ),
        migrations.CreateModel(
            name='OTPCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(
                    max_length=15,
                    validators=[django.core.validators.RegexValidator(
                        message="Telefon raqam to'g'ri formatda bo'lishi kerak. Masalan: +998901234567",
                        regex='^\\+\\d{10,15}$'
                    )]
                )),
                ('chat_id', models.CharField(max_length=20)),
                ('code', models.CharField(max_length=6)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'OTP Kod',
                'verbose_name_plural': 'OTP Kodlar',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PendingRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15, unique=True)),
                ('user_type', models.CharField(max_length=20)),
                ('first_name', models.CharField(blank=True, max_length=150)),
                ('last_name', models.CharField(blank=True, max_length=150)),
                ('middle_name', models.CharField(blank=True, max_length=150)),
                ('organization_name', models.CharField(blank=True, max_length=255, null=True)),
                ('position', models.CharField(blank=True, max_length=150, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': "Kutilayotgan Ro'yxat",
                'verbose_name_plural': "Kutilayotgan Ro'yxatlar",
            },
        ),
        migrations.CreateModel(
            name='OTPAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=15, unique=True)),
                ('attempts', models.IntegerField(default=0)),
                ('blocked_until', models.DateTimeField(blank=True, null=True)),
                ('last_attempt', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'OTP Urinish',
                'verbose_name_plural': 'OTP Urinishlar',
            },
        ),
        migrations.CreateModel(
            name='EmailVerificationCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('code', models.CharField(max_length=6)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('middle_name', models.CharField(blank=True, max_length=150)),
                ('password', models.CharField(max_length=255)),
                ('user_type', models.CharField(max_length=20)),
                ('organization_name', models.CharField(blank=True, max_length=255, null=True)),
                ('position', models.CharField(blank=True, max_length=150, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Email Tasdiqlash Kodi',
                'verbose_name_plural': 'Email Tasdiqlash Kodlari',
                'ordering': ['-created_at'],
            },
        ),
    ]
