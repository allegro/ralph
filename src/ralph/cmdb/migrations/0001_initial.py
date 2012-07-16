# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CIContentTypePrefix'
        db.create_table('cmdb_cicontenttypeprefix', (
            ('content_type_name', self.gf('django.db.models.fields.CharField')(max_length=255, primary_key=True)),
            ('prefix', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('cmdb', ['CIContentTypePrefix'])

        # Adding model 'CILayer'
        db.create_table('cmdb_cilayer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('cmdb', ['CILayer'])

        # Adding model 'CIRelation'
        db.create_table('cmdb_cirelation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'parent', to=orm['cmdb.CI'])),
            ('child', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'child', to=orm['cmdb.CI'])),
            ('type', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
        ))
        db.send_create_signal('cmdb', ['CIRelation'])

        # Adding unique constraint on 'CIRelation', fields ['parent', 'child', 'type']
        db.create_unique('cmdb_cirelation', ['parent_id', 'child_id', 'type'])

        # Adding model 'CIType'
        db.create_table('cmdb_citype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('cmdb', ['CIType'])

        # Adding model 'CIAttribute'
        db.create_table('cmdb_ciattribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('attribute_type', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('choices', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CIAttribute'])

        # Adding M2M table for field ci_types on 'CIAttribute'
        db.create_table('cmdb_ciattribute_ci_types', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('ciattribute', models.ForeignKey(orm['cmdb.ciattribute'], null=False)),
            ('citype', models.ForeignKey(orm['cmdb.citype'], null=False))
        ))
        db.create_unique('cmdb_ciattribute_ci_types', ['ciattribute_id', 'citype_id'])

        # Adding model 'CIValueDate'
        db.create_table('cmdb_civaluedate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CIValueDate'])

        # Adding model 'CIValueInteger'
        db.create_table('cmdb_civalueinteger', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CIValueInteger'])

        # Adding model 'CIValueFloat'
        db.create_table('cmdb_civaluefloat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CIValueFloat'])

        # Adding model 'CIValueString'
        db.create_table('cmdb_civaluestring', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CIValueString'])

        # Adding model 'CIValueChoice'
        db.create_table('cmdb_civaluechoice', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CIValueChoice'])

        # Adding model 'CIChangeZabbixTrigger'
        db.create_table('cmdb_cichangezabbixtrigger', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ci', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CI'], null=True)),
            ('trigger_id', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('host', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('host_id', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('status', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('lastchange', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('comments', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal('cmdb', ['CIChangeZabbixTrigger'])

        # Adding model 'CIChangeStatusOfficeIncident'
        db.create_table('cmdb_cichangestatusofficeincident', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ci', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CI'], null=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('subject', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('incident_id', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
        ))
        db.send_create_signal('cmdb', ['CIChangeStatusOfficeIncident'])

        # Adding model 'CIChange'
        db.create_table('cmdb_cichange', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ci', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CI'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('priority', self.gf('django.db.models.fields.IntegerField')(max_length=11)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=1024)),
        ))
        db.send_create_signal('cmdb', ['CIChange'])

        # Adding unique constraint on 'CIChange', fields ['content_type', 'object_id']
        db.create_unique('cmdb_cichange', ['content_type_id', 'object_id'])

        # Adding model 'CIChangeGit'
        db.create_table('cmdb_cichangegit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file_paths', self.gf('django.db.models.fields.CharField')(max_length=3000)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('changeset', self.gf('django.db.models.fields.CharField')(max_length=80)),
        ))
        db.send_create_signal('cmdb', ['CIChangeGit'])

        # Adding model 'CIChangePuppet'
        db.create_table('cmdb_cichangepuppet', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ci', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CI'], null=True, blank=True)),
            ('configuration_version', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('host', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('kind', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('cmdb', ['CIChangePuppet'])

        # Adding model 'PuppetLog'
        db.create_table('cmdb_puppetlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cichange', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIChangePuppet'])),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('message', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('tags', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('level', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('cmdb', ['PuppetLog'])

        # Adding model 'PuppetResourceStatus'
        db.create_table('cmdb_puppetresourcestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cichange', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIChangePuppet'])),
            ('change_count', self.gf('django.db.models.fields.IntegerField')()),
            ('changed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('failed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('skipped', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('file', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('line', self.gf('django.db.models.fields.IntegerField')()),
            ('resource', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('resource_type', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('cmdb', ['PuppetResourceStatus'])

        # Adding model 'CI'
        db.create_table('cmdb_ci', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uid', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('business_service', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('technical_service', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('pci_scope', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('barcode', self.gf('django.db.models.fields.CharField')(default=None, max_length=255, unique=True, null=True)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.IntegerField')(default=2, max_length=11)),
            ('status', self.gf('django.db.models.fields.IntegerField')(default=2, max_length=11)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIType'])),
            ('zabbix_id', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CI'])

        # Adding unique constraint on 'CI', fields ['content_type', 'object_id']
        db.create_unique('cmdb_ci', ['content_type_id', 'object_id'])

        # Adding M2M table for field layers on 'CI'
        db.create_table('cmdb_ci_layers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('ci', models.ForeignKey(orm['cmdb.ci'], null=False)),
            ('cilayer', models.ForeignKey(orm['cmdb.cilayer'], null=False))
        ))
        db.create_unique('cmdb_ci_layers', ['ci_id', 'cilayer_id'])

        # Adding model 'CIAttributeValue'
        db.create_table('cmdb_ciattributevalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ci', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CI'])),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIAttribute'])),
            ('value_integer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIValueInteger'], null=True, blank=True)),
            ('value_string', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIValueString'], null=True, blank=True)),
            ('value_date', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIValueDate'], null=True, blank=True)),
            ('value_float', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIValueFloat'], null=True, blank=True)),
            ('value_choice', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CIValueChoice'], null=True, blank=True)),
        ))
        db.send_create_signal('cmdb', ['CIAttributeValue'])

        # Adding model 'CIProblem'
        db.create_table('cmdb_ciproblem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ci', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CI'], null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('jira_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('assignee', self.gf('django.db.models.fields.CharField')(max_length=300)),
        ))
        db.send_create_signal('cmdb', ['CIProblem'])

        # Adding model 'CIIncident'
        db.create_table('cmdb_ciincident', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ci', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['cmdb.CI'], null=True, blank=True)),
            ('time', self.gf('django.db.models.fields.DateTimeField')()),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('jira_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('assignee', self.gf('django.db.models.fields.CharField')(max_length=300)),
        ))
        db.send_create_signal('cmdb', ['CIIncident'])


    def backwards(self, orm):
        # Removing unique constraint on 'CI', fields ['content_type', 'object_id']
        db.delete_unique('cmdb_ci', ['content_type_id', 'object_id'])

        # Removing unique constraint on 'CIChange', fields ['content_type', 'object_id']
        db.delete_unique('cmdb_cichange', ['content_type_id', 'object_id'])

        # Removing unique constraint on 'CIRelation', fields ['parent', 'child', 'type']
        db.delete_unique('cmdb_cirelation', ['parent_id', 'child_id', 'type'])

        # Deleting model 'CIContentTypePrefix'
        db.delete_table('cmdb_cicontenttypeprefix')

        # Deleting model 'CILayer'
        db.delete_table('cmdb_cilayer')

        # Deleting model 'CIRelation'
        db.delete_table('cmdb_cirelation')

        # Deleting model 'CIType'
        db.delete_table('cmdb_citype')

        # Deleting model 'CIAttribute'
        db.delete_table('cmdb_ciattribute')

        # Removing M2M table for field ci_types on 'CIAttribute'
        db.delete_table('cmdb_ciattribute_ci_types')

        # Deleting model 'CIValueDate'
        db.delete_table('cmdb_civaluedate')

        # Deleting model 'CIValueInteger'
        db.delete_table('cmdb_civalueinteger')

        # Deleting model 'CIValueFloat'
        db.delete_table('cmdb_civaluefloat')

        # Deleting model 'CIValueString'
        db.delete_table('cmdb_civaluestring')

        # Deleting model 'CIValueChoice'
        db.delete_table('cmdb_civaluechoice')

        # Deleting model 'CIChangeZabbixTrigger'
        db.delete_table('cmdb_cichangezabbixtrigger')

        # Deleting model 'CIChangeStatusOfficeIncident'
        db.delete_table('cmdb_cichangestatusofficeincident')

        # Deleting model 'CIChange'
        db.delete_table('cmdb_cichange')

        # Deleting model 'CIChangeGit'
        db.delete_table('cmdb_cichangegit')

        # Deleting model 'CIChangePuppet'
        db.delete_table('cmdb_cichangepuppet')

        # Deleting model 'PuppetLog'
        db.delete_table('cmdb_puppetlog')

        # Deleting model 'PuppetResourceStatus'
        db.delete_table('cmdb_puppetresourcestatus')

        # Deleting model 'CI'
        db.delete_table('cmdb_ci')

        # Removing M2M table for field layers on 'CI'
        db.delete_table('cmdb_ci_layers')

        # Deleting model 'CIAttributeValue'
        db.delete_table('cmdb_ciattributevalue')

        # Deleting model 'CIProblem'
        db.delete_table('cmdb_ciproblem')

        # Deleting model 'CIIncident'
        db.delete_table('cmdb_ciincident')


    models = {
        'cmdb.ci': {
            'Meta': {'unique_together': "((u'content_type', u'object_id'),)", 'object_name': 'CI'},
            'barcode': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'unique': 'True', 'null': 'True'}),
            'business_service': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'layers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cmdb.CILayer']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'pci_scope': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'relations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cmdb.CI']", 'through': "orm['cmdb.CIRelation']", 'symmetrical': 'False'}),
            'state': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '11'}),
            'status': ('django.db.models.fields.IntegerField', [], {'default': '2', 'max_length': '11'}),
            'technical_service': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIType']"}),
            'uid': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zabbix_id': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'})
        },
        'cmdb.ciattribute': {
            'Meta': {'object_name': 'CIAttribute'},
            'attribute_type': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'choices': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'ci_types': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['cmdb.CIType']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'cmdb.ciattributevalue': {
            'Meta': {'object_name': 'CIAttributeValue'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIAttribute']"}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value_choice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueChoice']", 'null': 'True', 'blank': 'True'}),
            'value_date': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueDate']", 'null': 'True', 'blank': 'True'}),
            'value_float': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueFloat']", 'null': 'True', 'blank': 'True'}),
            'value_integer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueInteger']", 'null': 'True', 'blank': 'True'}),
            'value_string': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIValueString']", 'null': 'True', 'blank': 'True'})
        },
        'cmdb.cichange': {
            'Meta': {'unique_together': "((u'content_type', u'object_id'),)", 'object_name': 'CIChange'},
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {'max_length': '11'})
        },
        'cmdb.cichangegit': {
            'Meta': {'object_name': 'CIChangeGit'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'changeset': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'file_paths': ('django.db.models.fields.CharField', [], {'max_length': '3000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'cmdb.cichangepuppet': {
            'Meta': {'object_name': 'CIChangePuppet'},
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'configuration_version': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cichangestatusofficeincident': {
            'Meta': {'object_name': 'CIChangeStatusOfficeIncident'},
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'incident_id': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'status': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cichangezabbixtrigger': {
            'Meta': {'object_name': 'CIChangeZabbixTrigger'},
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True'}),
            'comments': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'host_id': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastchange': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'status': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'trigger_id': ('django.db.models.fields.IntegerField', [], {'max_length': '11'})
        },
        'cmdb.cicontenttypeprefix': {
            'Meta': {'object_name': 'CIContentTypePrefix'},
            'content_type_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'primary_key': 'True'}),
            'prefix': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'cmdb.ciincident': {
            'Meta': {'object_name': 'CIIncident'},
            'assignee': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jira_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cilayer': {
            'Meta': {'object_name': 'CILayer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'cmdb.ciproblem': {
            'Meta': {'object_name': 'CIProblem'},
            'assignee': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jira_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.cirelation': {
            'Meta': {'unique_together': "((u'parent', u'child', u'type'),)", 'object_name': 'CIRelation'},
            'child': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'child'", 'to': "orm['cmdb.CI']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'parent'", 'to': "orm['cmdb.CI']"}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.IntegerField', [], {'max_length': '11'})
        },
        'cmdb.citype': {
            'Meta': {'object_name': 'CIType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.SlugField', [], {'max_length': '50'})
        },
        'cmdb.civaluechoice': {
            'Meta': {'object_name': 'CIValueChoice'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civaluedate': {
            'Meta': {'object_name': 'CIValueDate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civaluefloat': {
            'Meta': {'object_name': 'CIValueFloat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civalueinteger': {
            'Meta': {'object_name': 'CIValueInteger'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'cmdb.civaluestring': {
            'Meta': {'object_name': 'CIValueString'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'})
        },
        'cmdb.puppetlog': {
            'Meta': {'object_name': 'PuppetLog'},
            'cichange': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIChangePuppet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'time': ('django.db.models.fields.DateTimeField', [], {})
        },
        'cmdb.puppetresourcestatus': {
            'Meta': {'object_name': 'PuppetResourceStatus'},
            'change_count': ('django.db.models.fields.IntegerField', [], {}),
            'changed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cichange': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CIChangePuppet']"}),
            'failed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'file': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line': ('django.db.models.fields.IntegerField', [], {}),
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
        }
    }

    complete_apps = ['cmdb']