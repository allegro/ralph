# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CIValueFloat.created'
        db.add_column('cmdb_civaluefloat', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueFloat.modified'
        db.add_column('cmdb_civaluefloat', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueFloat.cache_version'
        db.add_column('cmdb_civaluefloat', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIContentTypePrefix.created'
        db.add_column('cmdb_cicontenttypeprefix', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIContentTypePrefix.modified'
        db.add_column('cmdb_cicontenttypeprefix', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIContentTypePrefix.cache_version'
        db.add_column('cmdb_cicontenttypeprefix', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIValueChoice.created'
        db.add_column('cmdb_civaluechoice', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueChoice.modified'
        db.add_column('cmdb_civaluechoice', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueChoice.cache_version'
        db.add_column('cmdb_civaluechoice', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIValueString.created'
        db.add_column('cmdb_civaluestring', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueString.modified'
        db.add_column('cmdb_civaluestring', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueString.cache_version'
        db.add_column('cmdb_civaluestring', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CI.created'
        db.add_column('cmdb_ci', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CI.modified'
        db.add_column('cmdb_ci', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CI.cache_version'
        db.add_column('cmdb_ci', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIChangeGit.created'
        db.add_column('cmdb_cichangegit', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangeGit.modified'
        db.add_column('cmdb_cichangegit', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangeGit.cache_version'
        db.add_column('cmdb_cichangegit', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'PuppetResourceStatus.created'
        db.add_column('cmdb_puppetresourcestatus', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'PuppetResourceStatus.modified'
        db.add_column('cmdb_puppetresourcestatus', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'PuppetResourceStatus.cache_version'
        db.add_column('cmdb_puppetresourcestatus', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'PuppetLog.created'
        db.add_column('cmdb_puppetlog', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'PuppetLog.modified'
        db.add_column('cmdb_puppetlog', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'PuppetLog.cache_version'
        db.add_column('cmdb_puppetlog', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CILayer.created'
        db.add_column('cmdb_cilayer', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CILayer.modified'
        db.add_column('cmdb_cilayer', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CILayer.cache_version'
        db.add_column('cmdb_cilayer', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIIncident.created'
        db.add_column('cmdb_ciincident', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIIncident.modified'
        db.add_column('cmdb_ciincident', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIIncident.cache_version'
        db.add_column('cmdb_ciincident', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIValueDate.created'
        db.add_column('cmdb_civaluedate', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueDate.modified'
        db.add_column('cmdb_civaluedate', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueDate.cache_version'
        db.add_column('cmdb_civaluedate', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIAttribute.created'
        db.add_column('cmdb_ciattribute', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIAttribute.modified'
        db.add_column('cmdb_ciattribute', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIAttribute.cache_version'
        db.add_column('cmdb_ciattribute', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIChangeZabbixTrigger.created'
        db.add_column('cmdb_cichangezabbixtrigger', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangeZabbixTrigger.modified'
        db.add_column('cmdb_cichangezabbixtrigger', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangeZabbixTrigger.cache_version'
        db.add_column('cmdb_cichangezabbixtrigger', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIProblem.created'
        db.add_column('cmdb_ciproblem', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIProblem.modified'
        db.add_column('cmdb_ciproblem', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIProblem.cache_version'
        db.add_column('cmdb_ciproblem', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIChangeStatusOfficeIncident.created'
        db.add_column('cmdb_cichangestatusofficeincident', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangeStatusOfficeIncident.modified'
        db.add_column('cmdb_cichangestatusofficeincident', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangeStatusOfficeIncident.cache_version'
        db.add_column('cmdb_cichangestatusofficeincident', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIChangePuppet.created'
        db.add_column('cmdb_cichangepuppet', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangePuppet.modified'
        db.add_column('cmdb_cichangepuppet', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChangePuppet.cache_version'
        db.add_column('cmdb_cichangepuppet', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIValueInteger.created'
        db.add_column('cmdb_civalueinteger', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueInteger.modified'
        db.add_column('cmdb_civalueinteger', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIValueInteger.cache_version'
        db.add_column('cmdb_civalueinteger', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIRelation.created'
        db.add_column('cmdb_cirelation', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIRelation.modified'
        db.add_column('cmdb_cirelation', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIRelation.cache_version'
        db.add_column('cmdb_cirelation', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIType.created'
        db.add_column('cmdb_citype', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIType.modified'
        db.add_column('cmdb_citype', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIType.cache_version'
        db.add_column('cmdb_citype', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIAttributeValue.created'
        db.add_column('cmdb_ciattributevalue', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIAttributeValue.modified'
        db.add_column('cmdb_ciattributevalue', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIAttributeValue.cache_version'
        db.add_column('cmdb_ciattributevalue', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)

        # Adding field 'CIChange.created'
        db.add_column('cmdb_cichange', 'created',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChange.modified'
        db.add_column('cmdb_cichange', 'modified',
                      self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now),
                      keep_default=False)

        # Adding field 'CIChange.cache_version'
        db.add_column('cmdb_cichange', 'cache_version',
                      self.gf('django.db.models.fields.PositiveIntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CIValueFloat.created'
        db.delete_column('cmdb_civaluefloat', 'created')

        # Deleting field 'CIValueFloat.modified'
        db.delete_column('cmdb_civaluefloat', 'modified')

        # Deleting field 'CIValueFloat.cache_version'
        db.delete_column('cmdb_civaluefloat', 'cache_version')

        # Deleting field 'CIContentTypePrefix.created'
        db.delete_column('cmdb_cicontenttypeprefix', 'created')

        # Deleting field 'CIContentTypePrefix.modified'
        db.delete_column('cmdb_cicontenttypeprefix', 'modified')

        # Deleting field 'CIContentTypePrefix.cache_version'
        db.delete_column('cmdb_cicontenttypeprefix', 'cache_version')

        # Deleting field 'CIValueChoice.created'
        db.delete_column('cmdb_civaluechoice', 'created')

        # Deleting field 'CIValueChoice.modified'
        db.delete_column('cmdb_civaluechoice', 'modified')

        # Deleting field 'CIValueChoice.cache_version'
        db.delete_column('cmdb_civaluechoice', 'cache_version')

        # Deleting field 'CIValueString.created'
        db.delete_column('cmdb_civaluestring', 'created')

        # Deleting field 'CIValueString.modified'
        db.delete_column('cmdb_civaluestring', 'modified')

        # Deleting field 'CIValueString.cache_version'
        db.delete_column('cmdb_civaluestring', 'cache_version')

        # Deleting field 'CI.created'
        db.delete_column('cmdb_ci', 'created')

        # Deleting field 'CI.modified'
        db.delete_column('cmdb_ci', 'modified')

        # Deleting field 'CI.cache_version'
        db.delete_column('cmdb_ci', 'cache_version')

        # Deleting field 'CIChangeGit.created'
        db.delete_column('cmdb_cichangegit', 'created')

        # Deleting field 'CIChangeGit.modified'
        db.delete_column('cmdb_cichangegit', 'modified')

        # Deleting field 'CIChangeGit.cache_version'
        db.delete_column('cmdb_cichangegit', 'cache_version')

        # Deleting field 'PuppetResourceStatus.created'
        db.delete_column('cmdb_puppetresourcestatus', 'created')

        # Deleting field 'PuppetResourceStatus.modified'
        db.delete_column('cmdb_puppetresourcestatus', 'modified')

        # Deleting field 'PuppetResourceStatus.cache_version'
        db.delete_column('cmdb_puppetresourcestatus', 'cache_version')

        # Deleting field 'PuppetLog.created'
        db.delete_column('cmdb_puppetlog', 'created')

        # Deleting field 'PuppetLog.modified'
        db.delete_column('cmdb_puppetlog', 'modified')

        # Deleting field 'PuppetLog.cache_version'
        db.delete_column('cmdb_puppetlog', 'cache_version')

        # Deleting field 'CILayer.created'
        db.delete_column('cmdb_cilayer', 'created')

        # Deleting field 'CILayer.modified'
        db.delete_column('cmdb_cilayer', 'modified')

        # Deleting field 'CILayer.cache_version'
        db.delete_column('cmdb_cilayer', 'cache_version')

        # Deleting field 'CIIncident.created'
        db.delete_column('cmdb_ciincident', 'created')

        # Deleting field 'CIIncident.modified'
        db.delete_column('cmdb_ciincident', 'modified')

        # Deleting field 'CIIncident.cache_version'
        db.delete_column('cmdb_ciincident', 'cache_version')

        # Deleting field 'CIValueDate.created'
        db.delete_column('cmdb_civaluedate', 'created')

        # Deleting field 'CIValueDate.modified'
        db.delete_column('cmdb_civaluedate', 'modified')

        # Deleting field 'CIValueDate.cache_version'
        db.delete_column('cmdb_civaluedate', 'cache_version')

        # Deleting field 'CIAttribute.created'
        db.delete_column('cmdb_ciattribute', 'created')

        # Deleting field 'CIAttribute.modified'
        db.delete_column('cmdb_ciattribute', 'modified')

        # Deleting field 'CIAttribute.cache_version'
        db.delete_column('cmdb_ciattribute', 'cache_version')

        # Deleting field 'CIChangeZabbixTrigger.created'
        db.delete_column('cmdb_cichangezabbixtrigger', 'created')

        # Deleting field 'CIChangeZabbixTrigger.modified'
        db.delete_column('cmdb_cichangezabbixtrigger', 'modified')

        # Deleting field 'CIChangeZabbixTrigger.cache_version'
        db.delete_column('cmdb_cichangezabbixtrigger', 'cache_version')

        # Deleting field 'CIProblem.created'
        db.delete_column('cmdb_ciproblem', 'created')

        # Deleting field 'CIProblem.modified'
        db.delete_column('cmdb_ciproblem', 'modified')

        # Deleting field 'CIProblem.cache_version'
        db.delete_column('cmdb_ciproblem', 'cache_version')

        # Deleting field 'CIChangeStatusOfficeIncident.created'
        db.delete_column('cmdb_cichangestatusofficeincident', 'created')

        # Deleting field 'CIChangeStatusOfficeIncident.modified'
        db.delete_column('cmdb_cichangestatusofficeincident', 'modified')

        # Deleting field 'CIChangeStatusOfficeIncident.cache_version'
        db.delete_column('cmdb_cichangestatusofficeincident', 'cache_version')

        # Deleting field 'CIChangePuppet.created'
        db.delete_column('cmdb_cichangepuppet', 'created')

        # Deleting field 'CIChangePuppet.modified'
        db.delete_column('cmdb_cichangepuppet', 'modified')

        # Deleting field 'CIChangePuppet.cache_version'
        db.delete_column('cmdb_cichangepuppet', 'cache_version')

        # Deleting field 'CIValueInteger.created'
        db.delete_column('cmdb_civalueinteger', 'created')

        # Deleting field 'CIValueInteger.modified'
        db.delete_column('cmdb_civalueinteger', 'modified')

        # Deleting field 'CIValueInteger.cache_version'
        db.delete_column('cmdb_civalueinteger', 'cache_version')

        # Deleting field 'CIRelation.created'
        db.delete_column('cmdb_cirelation', 'created')

        # Deleting field 'CIRelation.modified'
        db.delete_column('cmdb_cirelation', 'modified')

        # Deleting field 'CIRelation.cache_version'
        db.delete_column('cmdb_cirelation', 'cache_version')

        # Deleting field 'CIType.created'
        db.delete_column('cmdb_citype', 'created')

        # Deleting field 'CIType.modified'
        db.delete_column('cmdb_citype', 'modified')

        # Deleting field 'CIType.cache_version'
        db.delete_column('cmdb_citype', 'cache_version')

        # Deleting field 'CIAttributeValue.created'
        db.delete_column('cmdb_ciattributevalue', 'created')

        # Deleting field 'CIAttributeValue.modified'
        db.delete_column('cmdb_ciattributevalue', 'modified')

        # Deleting field 'CIAttributeValue.cache_version'
        db.delete_column('cmdb_ciattributevalue', 'cache_version')

        # Deleting field 'CIChange.created'
        db.delete_column('cmdb_cichange', 'created')

        # Deleting field 'CIChange.modified'
        db.delete_column('cmdb_cichange', 'modified')

        # Deleting field 'CIChange.cache_version'
        db.delete_column('cmdb_cichange', 'cache_version')


    models = {
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'max_length': '11'}),
            'time': ('django.db.models.fields.DateTimeField', [], {}),
            'type': ('django.db.models.fields.IntegerField', [], {'max_length': '11'})
        },
        'cmdb.cichangegit': {
            'Meta': {'object_name': 'CIChangeGit'},
            'author': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'changeset': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'file_paths': ('django.db.models.fields.CharField', [], {'max_length': '3000'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'cmdb.cichangepuppet': {
            'Meta': {'object_name': 'CIChangePuppet'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'ci': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['cmdb.CI']", 'null': 'True', 'blank': 'True'}),
            'configuration_version': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
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
        }
    }

    complete_apps = ['cmdb']