# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'ScanSummary.current_checksum'
        db.add_column('scan_scansummary', 'current_checksum',
                      self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ScanSummary.changed'
        db.add_column('scan_scansummary', 'changed',
                      self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True),
                      keep_default=False)


        # Changing field 'ScanSummary.previous_checksum'
        db.alter_column('scan_scansummary', 'previous_checksum', self.gf('django.db.models.fields.CharField')(max_length=32, null=True))

    def backwards(self, orm):
        # Deleting field 'ScanSummary.current_checksum'
        db.delete_column('scan_scansummary', 'current_checksum')

        # Deleting field 'ScanSummary.changed'
        db.delete_column('scan_scansummary', 'changed')


        # Changing field 'ScanSummary.previous_checksum'
        db.alter_column('scan_scansummary', 'previous_checksum', self.gf('django.db.models.fields.CharField')(default='-', max_length=32))

    models = {
        'scan.scansummary': {
            'Meta': {'object_name': 'ScanSummary'},
            'changed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'false_positive_checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '36'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'previous_checksum': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['scan']