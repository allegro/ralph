# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Venture.verified'
        db.add_column('business_venture', 'verified',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Venture.verified'
        db.delete_column('business_venture', 'verified')


    models = {
        'account.profile': {
            'Meta': {'object_name': 'Profile'},
            'activation_token': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '40', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'country': ('django.db.models.fields.PositiveIntegerField', [], {'default': '153'}),
            'gender': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2'}),
            'home_page': (u'dj.choices.fields.ChoiceField', [], {'unique': 'False', 'primary_key': 'False', 'db_column': 'None', 'blank': 'False', u'default': '1', 'null': 'False', '_in_south': 'True', 'db_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_active': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'nick': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '30', 'blank': 'True'}),
            'time_zone': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'business.businessline': {
            'Meta': {'object_name': 'BusinessLine'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        'business.businesssegment': {
            'Meta': {'object_name': 'BusinessSegment'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'business.department': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'Department'},
            'icon': (u'dj.choices.fields.ChoiceField', [], {'unique': 'False', 'primary_key': 'False', 'db_column': 'None', 'blank': 'True', u'default': 'None', 'null': 'True', '_in_south': 'True', 'db_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'business.profitcenter': {
            'Meta': {'object_name': 'ProfitCenter'},
            'description': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'business.roleproperty': {
            'Meta': {'unique_together': "[(u'symbol', u'role'), (u'symbol', u'venture')]", 'object_name': 'RoleProperty'},
            'default': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.VentureRole']", 'null': 'True', 'blank': 'True'}),
            'symbol': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '32', 'null': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.RolePropertyType']", 'null': 'True', 'blank': 'True'}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.Venture']", 'null': 'True', 'blank': 'True'})
        },
        'business.rolepropertytype': {
            'Meta': {'object_name': 'RolePropertyType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'symbol': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '32', 'unique': 'True', 'null': 'True'})
        },
        'business.rolepropertytypevalue': {
            'Meta': {'object_name': 'RolePropertyTypeValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.RolePropertyType']", 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'})
        },
        'business.rolepropertyvalue': {
            'Meta': {'unique_together': "((u'property', u'device'),)", 'object_name': 'RolePropertyValue'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.Device']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'property': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.RoleProperty']", 'null': 'True', 'blank': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True'})
        },
        'business.service': {
            'Meta': {'object_name': 'Service'},
            'business_line': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'business_person': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'business_person_mail': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'external_key': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'it_person': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'it_person_mail': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'business.venture': {
            'Meta': {'ordering': "(u'parent__symbol', u'symbol')", 'unique_together': "((u'parent', u'symbol'),)", 'object_name': 'Venture'},
            'business_segment': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.BusinessSegment']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'data_center': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['discovery.DataCenter']", 'null': 'True', 'blank': 'True'}),
            'department': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.Department']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_infrastructure': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'margin_kind': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.MarginKind']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "u'child_set'", 'null': 'True', 'blank': 'True', 'to': "orm['business.Venture']"}),
            'path': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'preboot': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['deployment.Preboot']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'profit_center': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.ProfitCenter']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'show_in_ralph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'symbol': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '32', 'blank': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'business.ventureextracost': {
            'Meta': {'ordering': "(u'type',)", 'unique_together': "((u'type', u'venture'),)", 'object_name': 'VentureExtraCost'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'cost': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'expire': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['business.VentureExtraCostType']"}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['business.Venture']"})
        },
        'business.ventureextracosttype': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'VentureExtraCostType'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'})
        },
        'business.venturerole': {
            'Meta': {'ordering': "(u'parent__name', u'name')", 'unique_together': "((u'name', u'venture'),)", 'object_name': 'VentureRole'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "u'child_set'", 'null': 'True', 'blank': 'True', 'to': "orm['business.VentureRole']"}),
            'path': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'preboot': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['deployment.Preboot']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['business.Venture']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'deployment.preboot': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'Preboot'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'files': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['deployment.PrebootFile']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'deployment.prebootfile': {
            'Meta': {'object_name': 'PrebootFile'},
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'default': 'None', 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ftype': (u'dj.choices.fields.ChoiceField', [], {'unique': 'False', 'primary_key': 'False', 'db_column': 'None', 'blank': 'False', u'default': '101', 'null': 'False', '_in_south': 'True', 'db_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'raw_config': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'discovery.datacenter': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'DataCenter'},
            'hosts_naming_template': ('django.db.models.fields.CharField', [], {'default': "u'h<10000,19999>.dc'", 'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'next_server': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '32', 'blank': 'True'})
        },
        'discovery.deprecationkind': {
            'Meta': {'object_name': 'DeprecationKind'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'months': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'})
        },
        'discovery.device': {
            'Meta': {'object_name': 'Device'},
            'barcode': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'boot_firmware': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'cached_cost': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'cached_price': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'chassis_position': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'dc': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'deprecation_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'deprecation_kind': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.DeprecationKind']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'diag_firmware': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'hard_firmware': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'management': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'managed_set'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['discovery.IPAddress']", 'blank': 'True', 'null': 'True'}),
            'margin_kind': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.MarginKind']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'max_save_priority': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'mgmt_firmware': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'model': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'device_set'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['discovery.DeviceModel']", 'blank': 'True', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name2': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'child_set'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': "orm['discovery.Device']", 'blank': 'True', 'null': 'True'}),
            'position': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'purchase_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'rack': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'save_priorities': ('django.db.models.fields.TextField', [], {'default': "u''"}),
            'sn': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'support_expiration_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'support_kind': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'uptime_seconds': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'uptime_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.Venture']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'venture_role': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.VentureRole']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'warranty_expiration_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'discovery.devicemodel': {
            'Meta': {'object_name': 'DeviceModel'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'chassis_size': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.DeviceModelGroup']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'max_save_priority': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'save_priorities': ('django.db.models.fields.TextField', [], {'default': "u''"}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '401'})
        },
        'discovery.devicemodelgroup': {
            'Meta': {'object_name': 'DeviceModelGroup'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slots': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '401'})
        },
        'discovery.discoveryqueue': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'DiscoveryQueue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'discovery.ipaddress': {
            'Meta': {'object_name': 'IPAddress'},
            'address': ('django.db.models.fields.IPAddressField', [], {'default': 'None', 'max_length': '15', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'dead_ping_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.Device']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'dns_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'http_family': ('django.db.models.fields.TextField', [], {'default': 'None', 'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_buried': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_plugins': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'last_puppet': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.Network']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'}),
            'snmp_community': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'snmp_name': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'snmp_version': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '5', 'null': 'True', 'blank': 'True'})
        },
        'discovery.marginkind': {
            'Meta': {'object_name': 'MarginKind'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'margin': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'})
        },
        'discovery.network': {
            'Meta': {'ordering': "(u'vlan',)", 'object_name': 'Network'},
            'address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '18'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'data_center': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['discovery.DataCenter']"}),
            'dhcp_config': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'gateway': ('django.db.models.fields.IPAddressField', [], {'default': 'None', 'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore_addresses': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.NetworkKind']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'last_scan': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'max_ip': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'min_ip': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'queue': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.DiscoveryQueue']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'racks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['discovery.Device']", 'symmetrical': 'False'}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'reserved': ('django.db.models.fields.PositiveIntegerField', [], {'default': '10'}),
            'reserved_top_margin': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'terminators': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['discovery.NetworkTerminator']", 'symmetrical': 'False'}),
            'vlan': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        },
        'discovery.networkkind': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'NetworkKind'},
            'icon': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'discovery.networkterminator': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'NetworkTerminator'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'tags.tag': {
            'Meta': {'object_name': 'Tag'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['account.Profile']"}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'tags_tag_tags'", 'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.PositiveIntegerField', [], {'default': '39'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'official': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'stem': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "u'related_tags'", 'null': 'True', 'to': "orm['tags.TagStem']"})
        },
        'tags.tagstem': {
            'Meta': {'object_name': 'TagStem'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.PositiveIntegerField', [], {'default': '39'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'tag_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        }
    }

    complete_apps = ['business']