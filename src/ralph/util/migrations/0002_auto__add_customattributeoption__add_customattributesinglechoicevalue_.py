# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CustomAttributeOption'
        db.create_table('util_customattributeoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('custom_attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['util.CustomAttribute'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('util', ['CustomAttributeOption'])

        # Adding model 'CustomAttributeSingleChoiceValue'
        db.create_table('util_customattributesinglechoicevalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['util.CustomAttribute'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('value', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['util.CustomAttributeOption'])),
        ))
        db.send_create_signal('util', ['CustomAttributeSingleChoiceValue'])

        # Adding model 'CustomAttributeIntegerValue'
        db.create_table('util_customattributeintegervalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['util.CustomAttribute'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('value', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('util', ['CustomAttributeIntegerValue'])

        # Adding model 'CustomAttributeStringValue'
        db.create_table('util_customattributestringvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attribute', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['util.CustomAttribute'])),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('util', ['CustomAttributeStringValue'])

        # Adding model 'CustomAttribute'
        db.create_table('util_customattribute', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('verbose_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('required', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('util', ['CustomAttribute'])


    def backwards(self, orm):
        # Deleting model 'CustomAttributeOption'
        db.delete_table('util_customattributeoption')

        # Deleting model 'CustomAttributeSingleChoiceValue'
        db.delete_table('util_customattributesinglechoicevalue')

        # Deleting model 'CustomAttributeIntegerValue'
        db.delete_table('util_customattributeintegervalue')

        # Deleting model 'CustomAttributeStringValue'
        db.delete_table('util_customattributestringvalue')

        # Deleting model 'CustomAttribute'
        db.delete_table('util_customattribute')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'util.customattribute': {
            'Meta': {'object_name': 'CustomAttribute'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'required': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'verbose_name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'util.customattributeintegervalue': {
            'Meta': {'object_name': 'CustomAttributeIntegerValue'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['util.CustomAttribute']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.IntegerField', [], {})
        },
        'util.customattributeoption': {
            'Meta': {'object_name': 'CustomAttributeOption'},
            'custom_attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['util.CustomAttribute']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'util.customattributesinglechoicevalue': {
            'Meta': {'object_name': 'CustomAttributeSingleChoiceValue'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['util.CustomAttribute']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['util.CustomAttributeOption']"})
        },
        'util.customattributestringvalue': {
            'Meta': {'object_name': 'CustomAttributeStringValue'},
            'attribute': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['util.CustomAttribute']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['util']