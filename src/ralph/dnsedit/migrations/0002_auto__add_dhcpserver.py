# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DHCPServer'
        db.create_table('dnsedit_dhcpserver', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(unique=True, max_length=15)),
            ('last_synchronized', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('dnsedit', ['DHCPServer'])


    def backwards(self, orm):
        # Deleting model 'DHCPServer'
        db.delete_table('dnsedit_dhcpserver')


    models = {
        'dnsedit.dhcpentry': {
            'Meta': {'object_name': 'DHCPEntry'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '15', 'blank': 'True'}),
            'mac': (u'lck.django.common.models.MACAddressField', [], {'unique': 'False', 'primary_key': 'False', 'db_column': 'None', 'blank': 'False', 'null': 'False', 'db_index': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        'dnsedit.dhcpserver': {
            'Meta': {'object_name': 'DHCPServer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'unique': 'True', 'max_length': '15'}),
            'last_synchronized': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['dnsedit']