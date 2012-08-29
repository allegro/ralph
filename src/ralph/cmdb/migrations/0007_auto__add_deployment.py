# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Deployment'
        db.create_table('cmdb_deployment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('cache_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['auth.User'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('status_lastchanged', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=1, max_length=11)),
            ('issue_key', self.gf('django.db.models.fields.CharField')(default=None, max_length=30, null=True, blank=True)),
            ('device', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['discovery.Device'])),
        ))
        db.send_create_signal('cmdb', ['Deployment'])


    def backwards(self, orm):
        # Deleting model 'Deployment'
        db.delete_table('cmdb_deployment')


    models = {
        'account.profile': {
            'Meta': {'object_name': 'Profile'},
            'activation_token': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '40', 'blank': 'True'}),
            'birth_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'country': ('django.db.models.fields.PositiveIntegerField', [], {'default': '153'}),
            'gender': ('django.db.models.fields.PositiveIntegerField', [], {'default': '2'}),
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
        'business.department': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'Department'},
            'icon': (u'dj.choices.fields.ChoiceField', [], {'unique': 'False', 'primary_key': 'False', 'db_column': 'None', 'blank': 'True', u'default': 'None', 'null': 'True', '_in_south': 'True', 'db_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'business.venture': {
            'Meta': {'unique_together': "((u'parent', u'symbol'),)", 'object_name': 'Venture'},
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
            'show_in_ralph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'symbol': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '32', 'blank': 'True'})
        },
        'business.venturerole': {
            'Meta': {'unique_together': "((u'name', u'venture'),)", 'object_name': 'VentureRole'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "u'child_set'", 'null': 'True', 'blank': 'True', 'to': "orm['business.VentureRole']"}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['business.Venture']"})
        },
        'cmdb.ci': {
            'Meta': {'unique_together': "((u'content_type', u'object_id'),)", 'object_name': 'CI'},
            'added_manually': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'barcode': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'business_service': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cmdb.CILayer']", 'symmetrical': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pci_scope': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'relations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cmdb.CI']", 'through': "orm['cmdb.CIRelation']", 'symmetrical': 'False'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '11'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '11'}),
            'technical_service': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIType']"}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'zabbix_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        'cmdb.ciattribute': {
            'Meta': {'object_name': 'CIAttribute'},
            'attribute_type': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'ci_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cmdb.CIType']", 'symmetrical': 'False'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'cmdb.ciattributevalue': {
            'Meta': {'object_name': 'CIAttributeValue'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIAttribute']"}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'value_choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueChoice']", 'null': 'True', 'blank': 'True'}),
            'value_date': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueDate']", 'null': 'True', 'blank': 'True'}),
            'value_float': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueFloat']", 'null': 'True', 'blank': 'True'}),
            'value_integer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueInteger']", 'null': 'True', 'blank': 'True'}),
            'value_string': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueString']", 'null': 'True', 'blank': 'True'})
        },
        'cmdb.cichange': {
            'Meta': {'unique_together': "((u'content_type', u'object_id'),)", 'object_name': 'CIChange'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'external_key': ('django.db.models.fields.CharField', [], {'max_length': '60', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'registration_type': ('django.db.models.fields.IntegerField', [], {'default': '4', 'max_length': '11'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {'max_length': '11'})
        },
        'cmdb.cichangecmdbhistory': {
            'Meta': {'object_name': 'CIChangeCMDBHistory'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'field_name': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '64'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'new_value': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255'}),
            'old_value': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255'}),
            'time': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'cmdb.cichangegit': {
            'Meta': {'object_name': 'CIChangeGit'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'changeset': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80', 'db_index': 'True'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'file_paths': ('django.db.models.fields.CharField', [], {'max_length': '3000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cichangepuppet': {
            'Meta': {'object_name': 'CIChangePuppet'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'configuration_version': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cichangestatusofficeincident': {
            'Meta': {'object_name': 'CIChangeStatusOfficeIncident'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incident_id': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cichangezabbixtrigger': {
            'Meta': {'object_name': 'CIChangeZabbixTrigger'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True'}),
            'comments': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'host_id': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastchange': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'status': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'trigger_id': ('django.db.models.fields.IntegerField', [], {'max_length': '11'})
        },
        'cmdb.cicontenttypeprefix': {
            'Meta': {'object_name': 'CIContentTypePrefix'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'content_type_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'primary_key': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'prefix': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'cmdb.ciincident': {
            'Meta': {'object_name': 'CIIncident'},
            'assignee': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jira_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cilayer': {
            'Meta': {'object_name': 'CILayer'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'cmdb.ciproblem': {
            'Meta': {'object_name': 'CIProblem'},
            'assignee': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jira_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cirelation': {
            'Meta': {'unique_together': "((u'parent', u'child', u'type'),)", 'object_name': 'CIRelation'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'child'", 'to': "orm['cmdb.CI']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'parent'", 'to': "orm['cmdb.CI']"}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.IntegerField', [], {'max_length': '11'})
        },
        'cmdb.citype': {
            'Meta': {'object_name': 'CIType'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'cmdb.civaluechoice': {
            'Meta': {'object_name': 'CIValueChoice'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civaluedate': {
            'Meta': {'object_name': 'CIValueDate'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civaluefloat': {
            'Meta': {'object_name': 'CIValueFloat'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civalueinteger': {
            'Meta': {'object_name': 'CIValueInteger'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civaluestring': {
            'Meta': {'object_name': 'CIValueString'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'})
        },
        'cmdb.deployment': {
            'Meta': {'object_name': 'Deployment'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['discovery.Device']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issue_key': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '1', 'max_length': '11'}),
            'status_lastchanged': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'})
        },
        'cmdb.puppetlog': {
            'Meta': {'object_name': 'PuppetLog'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'cichange': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIChangePuppet']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.puppetresourcestatus': {
            'Meta': {'object_name': 'PuppetResourceStatus'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'change_count': ('django.db.models.fields.IntegerField', [], {}),
            'changed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cichange': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIChangePuppet']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'file': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.IntegerField', [], {}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'resource': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'resource_type': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'skipped': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'discovery.datacenter': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'DataCenter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'discovery.deprecationkind': {
            'Meta': {'object_name': 'DeprecationKind'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'raw': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'save_priorities': ('django.db.models.fields.TextField', [], {'default': "u''"}),
            'sn': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'support_expiration_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'support_kind': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'price': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slots': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '401'})
        },
        'discovery.ipaddress': {
            'Meta': {'object_name': 'IPAddress'},
            'address': ('django.db.models.fields.IPAddressField', [], {'default': 'None', 'max_length': '15', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.Device']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'dns_info': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'http_family': ('django.db.models.fields.TextField', [], {'default': 'None', 'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_management': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_puppet': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'last_seen': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'network': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.Network']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'}),
            'snmp_community': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'snmp_name': ('django.db.models.fields.TextField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
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
            'gateway': ('django.db.models.fields.IPAddressField', [], {'default': 'None', 'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.NetworkKind']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'max_ip': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'min_ip': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'queue': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'rack': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'remarks': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
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

    complete_apps = ['cmdb']