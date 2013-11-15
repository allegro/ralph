# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ScanSummary'
        db.create_table('scan_scansummary', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('job_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=36)),
            ('previous_checksum', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('false_positive_checksum', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('scan', ['ScanSummary'])


    def backwards(self, orm):
        # Deleting model 'ScanSummary'
        db.delete_table('scan_scansummary')


    models = {
        'scan.scansummary': {
            'Meta': {'object_name': 'ScanSummary'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'false_positive_checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'previous_checksum': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['scan']