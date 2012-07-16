# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DHCPEntry'
        db.create_table('dnsedit_dhcpentry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('cache_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('mac', self.gf(u'lck.django.common.models.MACAddressField')(unique=False, primary_key=False, db_column=None, blank=False, null=False, db_index=False)),
            ('ip', self.gf('django.db.models.fields.CharField')(default=u'', max_length=15, blank=True)),
        ))
        db.send_create_signal('dnsedit', ['DHCPEntry'])


    def backwards(self, orm):
        # Deleting model 'DHCPEntry'
        db.delete_table('dnsedit_dhcpentry')


    models = {
        'dnsedit.dhcpentry': {
            'Meta': {'object_name': 'DHCPEntry'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '15', 'blank': 'True'}),
            'mac': (u'lck.django.common.models.MACAddressField', [], {'unique': 'False', 'primary_key': 'False', 'db_column': 'None', 'blank': 'False', 'null': 'False', 'db_index': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        }
    }

    complete_apps = ['dnsedit']