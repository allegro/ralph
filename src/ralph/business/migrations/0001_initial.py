# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Venture'
        db.create_table('business_venture', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=75, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('cache_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('data_center', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['discovery.DataCenter'], null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name=u'child_set', null=True, blank=True, to=orm['business.Venture'])),
            ('symbol', self.gf('django.db.models.fields.CharField')(default=u'', max_length=32, blank=True)),
            ('show_in_ralph', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_infrastructure', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('margin_kind', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['discovery.MarginKind'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('department', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['business.Department'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('path', self.gf('django.db.models.fields.TextField')(default=u'', blank=True)),
            ('img_path', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
            ('kickstart_path', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
        ))
        db.send_create_signal('business', ['Venture'])

        # Adding unique constraint on 'Venture', fields ['parent', 'symbol']
        db.create_unique('business_venture', ['parent_id', 'symbol'])

        # Adding M2M table for field networks on 'Venture'
        db.create_table('business_venture_networks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('venture', models.ForeignKey(orm['business.venture'], null=False)),
            ('network', models.ForeignKey(orm['discovery.network'], null=False))
        ))
        db.create_unique('business_venture_networks', ['venture_id', 'network_id'])

        # Adding model 'Service'
        db.create_table('business_service', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('external_key', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100, db_index=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('it_person', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
            ('it_person_mail', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
            ('business_person', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
            ('business_person_mail', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
            ('business_line', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('business', ['Service'])

        # Adding model 'BusinessLine'
        db.create_table('business_businessline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
        ))
        db.send_create_signal('business', ['BusinessLine'])

        # Adding model 'VentureRole'
        db.create_table('business_venturerole', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=75)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('cache_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('venture', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['business.Venture'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name=u'child_set', null=True, blank=True, to=orm['business.VentureRole'])),
            ('img_path', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
            ('kickstart_path', self.gf('django.db.models.fields.CharField')(default=u'', max_length=255, blank=True)),
        ))
        db.send_create_signal('business', ['VentureRole'])

        # Adding unique constraint on 'VentureRole', fields ['name', 'venture']
        db.create_unique('business_venturerole', ['name', 'venture_id'])

        # Adding M2M table for field networks on 'VentureRole'
        db.create_table('business_venturerole_networks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('venturerole', models.ForeignKey(orm['business.venturerole'], null=False)),
            ('network', models.ForeignKey(orm['discovery.network'], null=False))
        ))
        db.create_unique('business_venturerole_networks', ['venturerole_id', 'network_id'])

        # Adding model 'RolePropertyType'
        db.create_table('business_rolepropertytype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('symbol', self.gf('django.db.models.fields.CharField')(default=None, max_length=32, unique=True, null=True)),
        ))
        db.send_create_signal('business', ['RolePropertyType'])

        # Adding model 'RolePropertyTypeValue'
        db.create_table('business_rolepropertytypevalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['business.RolePropertyType'], null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
        ))
        db.send_create_signal('business', ['RolePropertyTypeValue'])

        # Adding model 'RoleProperty'
        db.create_table('business_roleproperty', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('symbol', self.gf('django.db.models.fields.CharField')(default=None, max_length=32, null=True)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['business.VentureRole'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['business.RolePropertyType'], null=True, blank=True)),
        ))
        db.send_create_signal('business', ['RoleProperty'])

        # Adding unique constraint on 'RoleProperty', fields ['symbol', 'role']
        db.create_unique('business_roleproperty', ['symbol', 'role_id'])

        # Adding model 'RolePropertyValue'
        db.create_table('business_rolepropertyvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('property', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['business.RoleProperty'], null=True, blank=True)),
            ('device', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['discovery.Device'], null=True, blank=True)),
            ('value', self.gf('django.db.models.fields.TextField')(default=None, null=True)),
        ))
        db.send_create_signal('business', ['RolePropertyValue'])

        # Adding unique constraint on 'RolePropertyValue', fields ['property', 'device']
        db.create_unique('business_rolepropertyvalue', ['property_id', 'device_id'])

        # Adding model 'VentureOwner'
        db.create_table('business_ventureowner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=75)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('cache_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('venture', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['business.Venture'])),
            ('type', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('synergy_id', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('business', ['VentureOwner'])

        # Adding model 'Department'
        db.create_table('business_department', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=75, db_index=True)),
            ('icon', self.gf(u'dj.choices.fields.ChoiceField')(unique=False, primary_key=False, db_column=None, blank=True, default=None, null=True, _in_south=True, db_index=False)),
        ))
        db.send_create_signal('business', ['Department'])

        # Adding model 'VentureExtraCost'
        db.create_table('business_ventureextracost', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=75)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('cache_version', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('venture', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['business.Venture'])),
            ('cost', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('expire', self.gf('django.db.models.fields.DateField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal('business', ['VentureExtraCost'])

        # Adding unique constraint on 'VentureExtraCost', fields ['name', 'venture']
        db.create_unique('business_ventureextracost', ['name', 'venture_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'VentureExtraCost', fields ['name', 'venture']
        db.delete_unique('business_ventureextracost', ['name', 'venture_id'])

        # Removing unique constraint on 'RolePropertyValue', fields ['property', 'device']
        db.delete_unique('business_rolepropertyvalue', ['property_id', 'device_id'])

        # Removing unique constraint on 'RoleProperty', fields ['symbol', 'role']
        db.delete_unique('business_roleproperty', ['symbol', 'role_id'])

        # Removing unique constraint on 'VentureRole', fields ['name', 'venture']
        db.delete_unique('business_venturerole', ['name', 'venture_id'])

        # Removing unique constraint on 'Venture', fields ['parent', 'symbol']
        db.delete_unique('business_venture', ['parent_id', 'symbol'])

        # Deleting model 'Venture'
        db.delete_table('business_venture')

        # Removing M2M table for field networks on 'Venture'
        db.delete_table('business_venture_networks')

        # Deleting model 'Service'
        db.delete_table('business_service')

        # Deleting model 'BusinessLine'
        db.delete_table('business_businessline')

        # Deleting model 'VentureRole'
        db.delete_table('business_venturerole')

        # Removing M2M table for field networks on 'VentureRole'
        db.delete_table('business_venturerole_networks')

        # Deleting model 'RolePropertyType'
        db.delete_table('business_rolepropertytype')

        # Deleting model 'RolePropertyTypeValue'
        db.delete_table('business_rolepropertytypevalue')

        # Deleting model 'RoleProperty'
        db.delete_table('business_roleproperty')

        # Deleting model 'RolePropertyValue'
        db.delete_table('business_rolepropertyvalue')

        # Deleting model 'VentureOwner'
        db.delete_table('business_ventureowner')

        # Deleting model 'Department'
        db.delete_table('business_department')

        # Deleting model 'VentureExtraCost'
        db.delete_table('business_ventureextracost')


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
        'business.businessline': {
            'Meta': {'object_name': 'BusinessLine'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        'business.department': {
            'Meta': {'ordering': "(u'name',)", 'object_name': 'Department'},
            'icon': (u'dj.choices.fields.ChoiceField', [], {'unique': 'False', 'primary_key': 'False', 'db_column': 'None', 'blank': 'True', u'default': 'None', 'null': 'True', '_in_south': 'True', 'db_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'})
        },
        'business.roleproperty': {
            'Meta': {'unique_together': "((u'symbol', u'role'),)", 'object_name': 'RoleProperty'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.VentureRole']", 'null': 'True', 'blank': 'True'}),
            'symbol': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '32', 'null': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.RolePropertyType']", 'null': 'True', 'blank': 'True'})
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
            'device': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.Device']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'Meta': {'unique_together': "((u'parent', u'symbol'),)", 'object_name': 'Venture'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'data_center': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['discovery.DataCenter']", 'null': 'True', 'blank': 'True'}),
            'department': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['business.Department']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'img_path': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'is_infrastructure': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'kickstart_path': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'margin_kind': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['discovery.MarginKind']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75', 'db_index': 'True'}),
            'networks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['discovery.Network']", 'null': 'True', 'symmetrical': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "u'child_set'", 'null': 'True', 'blank': 'True', 'to': "orm['business.Venture']"}),
            'path': ('django.db.models.fields.TextField', [], {'default': "u''", 'blank': 'True'}),
            'show_in_ralph': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'symbol': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '32', 'blank': 'True'})
        },
        'business.ventureextracost': {
            'Meta': {'ordering': "(u'name',)", 'unique_together': "((u'name', u'venture'),)", 'object_name': 'VentureExtraCost'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'cost': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'expire': ('django.db.models.fields.DateField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['business.Venture']"})
        },
        'business.ventureowner': {
            'Meta': {'object_name': 'VentureOwner'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'synergy_id': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['business.Venture']"})
        },
        'business.venturerole': {
            'Meta': {'unique_together': "((u'name', u'venture'),)", 'object_name': 'VentureRole'},
            'cache_version': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'img_path': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'kickstart_path': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '255', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'networks': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['discovery.Network']", 'null': 'True', 'symmetrical': 'False'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "u'child_set'", 'null': 'True', 'blank': 'True', 'to': "orm['business.VentureRole']"}),
            'venture': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['business.Venture']"})
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

    complete_apps = ['business']