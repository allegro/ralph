# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models
import django.core.validators
import django.utils.timezone
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='RalphUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status', default=False)),
                ('username', models.CharField(verbose_name='username', error_messages={'unique': 'A user with that username already exists.'}, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.', 'invalid')], max_length=30, unique=True, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.')),
                ('first_name', models.CharField(blank=True, verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(blank=True, verbose_name='last name', max_length=30)),
                ('email', models.EmailField(blank=True, verbose_name='email address', max_length=254)),
                ('is_staff', models.BooleanField(help_text='Designates whether the user can log into this admin site.', verbose_name='staff status', default=False)),
                ('is_active', models.BooleanField(help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active', default=True)),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('gender', models.PositiveIntegerField(choices=[(1, 'female'), (2, 'male'), (3, 'unspecified')], verbose_name='gender', default=2)),
                ('country', models.PositiveIntegerField(choices=[(1, 'Afghanistan'), (2, 'Albania'), (3, 'Algeria'), (4, 'American Samoa'), (5, 'Andorra'), (6, 'Angola'), (7, 'Anguilla'), (8, 'Antarctica'), (9, 'Antigua and Barbuda'), (10, 'Argentina'), (11, 'Armenia'), (12, 'Aruba'), (13, 'Australia'), (14, 'Austria'), (15, 'Azerbaijan'), (16, 'Bahamas'), (17, 'Bahrain'), (18, 'Bangladesh'), (19, 'Barbados'), (20, 'Belarus'), (21, 'Belgium'), (22, 'Belize'), (23, 'Benin'), (24, 'Bermuda'), (25, 'Bhutan'), (26, 'Bolivia'), (27, 'Bosnia and Herzegovina'), (28, 'Botswana'), (29, 'Brazil'), (30, 'Brunei'), (31, 'Bulgaria'), (32, 'Burkina Faso'), (33, 'Burundi'), (34, 'Cambodia'), (35, 'Cameroon'), (36, 'Canada'), (37, 'Cape Verde'), (38, 'Cayman Islands'), (39, 'Central African Republic'), (40, 'Chad'), (41, 'Chile'), (42, 'China'), (43, 'Colombia'), (44, 'Comoros'), (45, 'Congo Brazzaville'), (46, 'Congo Kinshasa'), (47, 'Cook Islands'), (48, 'Costa Rica'), (49, 'Cote Divoire'), (50, 'Croatia'), (51, 'Cuba'), (52, 'Cyprus'), (53, 'Czech Republic'), (54, 'Denmark'), (55, 'Djibouti'), (56, 'Dominica'), (57, 'Dominican Republic'), (58, 'Ecuador'), (59, 'Egypt'), (60, 'El Salvador'), (61, 'Equatorial Guinea'), (62, 'Eritrea'), (63, 'Estonia'), (64, 'Ethiopia'), (65, 'Faroe Islands'), (66, 'Fiji'), (67, 'Finland'), (68, 'France'), (69, 'French Polynesia'), (70, 'Gabon'), (71, 'Gambia'), (72, 'Georgia'), (73, 'Germany'), (74, 'Ghana'), (75, 'Gibraltar'), (76, 'Greece'), (77, 'Grenada'), (78, 'Guam'), (79, 'Guatemala'), (80, 'Guinea Bissau'), (81, 'Guinea'), (82, 'Guyana'), (83, 'Haiti'), (84, 'Honduras'), (85, 'Hong Kong'), (86, 'Hungary'), (87, 'Iceland'), (88, 'India'), (89, 'Indonesia'), (90, 'Iran'), (91, 'Iraq'), (92, 'Ireland'), (93, 'Israel'), (94, 'Italy'), (95, 'Jamaica'), (96, 'Japan'), (97, 'Jersey'), (98, 'Jordan'), (99, 'Kazakhstan'), (100, 'Kenya'), (101, 'Kiribati'), (102, 'Kuwait'), (103, 'Kyrgyzstan'), (104, 'Laos'), (105, 'Latvia'), (106, 'Lebanon'), (107, 'Lesotho'), (108, 'Liberia'), (109, 'Libya'), (110, 'Liechtenstein'), (111, 'Lithuania'), (112, 'Luxembourg'), (113, 'Macau'), (114, 'Macedonia'), (115, 'Madagascar'), (116, 'Malawi'), (117, 'Malaysia'), (118, 'Maldives'), (119, 'Mali'), (120, 'Malta'), (121, 'Marshall Islands'), (122, 'Mauritania'), (123, 'Mauritius'), (124, 'Mexico'), (125, 'Micronesia'), (126, 'Moldova'), (127, 'Monaco'), (128, 'Mongolia'), (129, 'Montenegro'), (130, 'Montserrat'), (131, 'Morocco'), (132, 'Mozambique'), (133, 'Myanmar'), (134, 'Namibia'), (135, 'Nauru'), (136, 'Nepal'), (137, 'Netherlands Antilles'), (138, 'Netherlands'), (139, 'New Zealand'), (140, 'Nicaragua'), (141, 'Niger'), (142, 'Nigeria'), (143, 'North Korea'), (144, 'Norway'), (145, 'Oman'), (146, 'Pakistan'), (147, 'Palau'), (148, 'Panama'), (149, 'Papua New Guinea'), (150, 'Paraguay'), (151, 'Peru'), (152, 'Philippines'), (153, 'Poland'), (154, 'Portugal'), (155, 'Puerto Rico'), (156, 'Qatar'), (157, 'Romania'), (158, 'Russian Federation'), (159, 'Rwanda'), (160, 'Saint Lucia'), (161, 'Samoa'), (162, 'San Marino'), (163, 'Sao Tome and Principe'), (164, 'Saudi Arabia'), (165, 'Senegal'), (166, 'Serbia'), (167, 'Seychelles'), (168, 'Sierra Leone'), (169, 'Singapore'), (170, 'Slovakia'), (171, 'Slovenia'), (172, 'Solomon Islands'), (173, 'Somalia'), (174, 'South Africa'), (175, 'South Korea'), (176, 'Spain'), (177, 'Sri Lanka'), (178, 'St Kitts and Nevis'), (179, 'St Vincent and the Grenadines'), (180, 'Sudan'), (181, 'Suriname'), (182, 'Swaziland'), (183, 'Sweden'), (184, 'Switzerland'), (185, 'Syria'), (186, 'Tajikistan'), (187, 'Taiwan'), (188, 'Tanzania'), (189, 'Thailand'), (190, 'Timor Leste'), (191, 'Togo'), (192, 'Tonga'), (193, 'Trinidad and Tobago'), (194, 'Tunisia'), (195, 'Turkey'), (196, 'Turkmenistan'), (197, 'Turks and Caicos Islands'), (198, 'Tuvalu'), (199, 'Uganda'), (200, 'Ukraine'), (201, 'United Arab Emirates'), (202, 'United Kingdom'), (203, 'United States of America'), (204, 'Uruguay'), (205, 'Uzbekistan'), (206, 'Vanuatu'), (207, 'Vatican City'), (208, 'Venezuela'), (209, 'Viet Nam'), (210, 'Virgin Islands British'), (211, 'Virgin Islands US'), (212, 'Western Sahara'), (213, 'Yemen'), (214, 'Zambia'), (215, 'Zimbabwe'), (301, 'England'), (302, 'Northern Ireland'), (303, 'Wales'), (304, 'Scotland'), (601, 'Northern Cyprus'), (602, 'Palestine'), (603, 'Somaliland'), (901, 'African Union'), (902, 'Arab League'), (903, 'Association of Southeast Asian Nations'), (904, 'Caricom'), (905, 'Commonwealth of Independent States'), (906, 'Commonwealth of Nations'), (907, 'European Union'), (908, 'Islamic Conference'), (909, 'NATO'), (910, 'Olimpic Movement'), (911, 'OPEC'), (912, 'Red Cross'), (913, 'United Nations')], verbose_name='country', default=153)),
                ('city', models.CharField(blank=True, verbose_name='city', max_length=30)),
                ('company', models.CharField(blank=True, verbose_name='company', max_length=64)),
                ('employee_id', models.CharField(blank=True, verbose_name='employee id', max_length=64)),
                ('profit_center', models.CharField(blank=True, verbose_name='profit center', max_length=1024)),
                ('cost_center', models.CharField(blank=True, verbose_name='cost center', max_length=1024)),
                ('department', models.CharField(blank=True, verbose_name='department', max_length=64)),
                ('manager', models.CharField(blank=True, verbose_name='manager', max_length=1024)),
                ('location', models.CharField(blank=True, verbose_name='location', max_length=128)),
                ('segment', models.CharField(blank=True, verbose_name='segment', max_length=256)),
                ('groups', models.ManyToManyField(related_name='user_set', related_query_name='user', verbose_name='groups', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', to='auth.Group', blank=True)),
            ],
            options={
                'verbose_name_plural': 'users',
                'verbose_name': 'user',
                'abstract': False,
                'swappable': 'AUTH_USER_MODEL',
            },
            bases=(models.Model, ralph.lib.mixins.models.AdminAbsoluteUrlMixin),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(unique=True, verbose_name='name', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(unique=True, verbose_name='name', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='ralphuser',
            name='regions',
            field=models.ManyToManyField(related_name='users', to='accounts.Region', blank=True),
        ),
        migrations.AddField(
            model_name='ralphuser',
            name='team',
            field=models.ForeignKey(null=True, to='accounts.Team', blank=True),
        ),
        migrations.AddField(
            model_name='ralphuser',
            name='user_permissions',
            field=models.ManyToManyField(related_name='user_set', related_query_name='user', verbose_name='user permissions', help_text='Specific permissions for this user.', to='auth.Permission', blank=True),
        ),
    ]
