# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'BaseEvent'
        db.create_table('condottieri_events_baseevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Game'])),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('season', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('phase', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('condottieri_events', ['BaseEvent'])

        # Adding model 'NewUnitEvent'
        db.create_table('condottieri_events_newunitevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('condottieri_events', ['NewUnitEvent'])

        # Adding model 'DisbandEvent'
        db.create_table('condottieri_events_disbandevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('condottieri_events', ['DisbandEvent'])

        # Adding model 'OrderEvent'
        db.create_table('condottieri_events_orderevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='event_origin', to=orm['machiavelli.Area'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='event_destination', null=True, to=orm['machiavelli.Area'])),
            ('conversion', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('subtype', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('suborigin', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='event_suborigin', null=True, to=orm['machiavelli.Area'])),
            ('subcode', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('subdestination', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='event_subdestination', null=True, to=orm['machiavelli.Area'])),
            ('subconversion', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
        ))
        db.send_create_signal('condottieri_events', ['OrderEvent'])

        # Adding model 'StandoffEvent'
        db.create_table('condottieri_events_standoffevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('condottieri_events', ['StandoffEvent'])

        # Adding model 'ConversionEvent'
        db.create_table('condottieri_events_conversionevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
            ('before', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('after', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('condottieri_events', ['ConversionEvent'])

        # Adding model 'ControlEvent'
        db.create_table('condottieri_events_controlevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('condottieri_events', ['ControlEvent'])

        # Adding model 'MovementEvent'
        db.create_table('condottieri_events_movementevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='movement_origin', to=orm['machiavelli.Area'])),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(related_name='movement_destination', to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('condottieri_events', ['MovementEvent'])

        # Adding model 'RetreatEvent'
        db.create_table('condottieri_events_retreatevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='retreat_origin', to=orm['machiavelli.Area'])),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(related_name='retreat_destination', to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('condottieri_events', ['RetreatEvent'])

        # Adding model 'UnitEvent'
        db.create_table('condottieri_events_unitevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
            ('message', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('condottieri_events', ['UnitEvent'])

        # Adding model 'CountryEvent'
        db.create_table('condottieri_events_countryevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['condottieri_events.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('message', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('condottieri_events', ['CountryEvent'])


    def backwards(self, orm):
        
        # Deleting model 'BaseEvent'
        db.delete_table('condottieri_events_baseevent')

        # Deleting model 'NewUnitEvent'
        db.delete_table('condottieri_events_newunitevent')

        # Deleting model 'DisbandEvent'
        db.delete_table('condottieri_events_disbandevent')

        # Deleting model 'OrderEvent'
        db.delete_table('condottieri_events_orderevent')

        # Deleting model 'StandoffEvent'
        db.delete_table('condottieri_events_standoffevent')

        # Deleting model 'ConversionEvent'
        db.delete_table('condottieri_events_conversionevent')

        # Deleting model 'ControlEvent'
        db.delete_table('condottieri_events_controlevent')

        # Deleting model 'MovementEvent'
        db.delete_table('condottieri_events_movementevent')

        # Deleting model 'RetreatEvent'
        db.delete_table('condottieri_events_retreatevent')

        # Deleting model 'UnitEvent'
        db.delete_table('condottieri_events_unitevent')

        # Deleting model 'CountryEvent'
        db.delete_table('condottieri_events_countryevent')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'condottieri_events.baseevent': {
            'Meta': {'object_name': 'BaseEvent'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phase': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'season': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'condottieri_events.controlevent': {
            'Meta': {'object_name': 'ControlEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"})
        },
        'condottieri_events.conversionevent': {
            'Meta': {'object_name': 'ConversionEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'after': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'before': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'condottieri_events.countryevent': {
            'Meta': {'object_name': 'CountryEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"}),
            'message': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'condottieri_events.disbandevent': {
            'Meta': {'object_name': 'DisbandEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'condottieri_events.movementevent': {
            'Meta': {'object_name': 'MovementEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'movement_destination'", 'to': "orm['machiavelli.Area']"}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'movement_origin'", 'to': "orm['machiavelli.Area']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'condottieri_events.newunitevent': {
            'Meta': {'object_name': 'NewUnitEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'condottieri_events.orderevent': {
            'Meta': {'object_name': 'OrderEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'conversion': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_destination'", 'null': 'True', 'to': "orm['machiavelli.Area']"}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'event_origin'", 'to': "orm['machiavelli.Area']"}),
            'subcode': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'subconversion': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'subdestination': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_subdestination'", 'null': 'True', 'to': "orm['machiavelli.Area']"}),
            'suborigin': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'event_suborigin'", 'null': 'True', 'to': "orm['machiavelli.Area']"}),
            'subtype': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'condottieri_events.retreatevent': {
            'Meta': {'object_name': 'RetreatEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'retreat_destination'", 'to': "orm['machiavelli.Area']"}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'retreat_origin'", 'to': "orm['machiavelli.Area']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'condottieri_events.standoffevent': {
            'Meta': {'object_name': 'StandoffEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'})
        },
        'condottieri_events.unitevent': {
            'Meta': {'object_name': 'UnitEvent', '_ormbases': ['condottieri_events.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['condottieri_events.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'message': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'machiavelli.area': {
            'Meta': {'object_name': 'Area'},
            'borders': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'borders_rel_+'", 'to': "orm['machiavelli.Area']"}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '5'}),
            'has_city': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'has_port': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_coast': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_fortified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_sea': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'name': ('machiavelli.fields.AutoTranslateField', [], {'unique': 'True', 'max_length': '25'})
        },
        'machiavelli.country': {
            'Meta': {'object_name': 'Country'},
            'css_class': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('machiavelli.fields.AutoTranslateField', [], {'unique': 'True', 'max_length': '20'})
        },
        'machiavelli.game': {
            'Meta': {'object_name': 'Game'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_phase_change': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'map_outdated': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'phase': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Scenario']"}),
            'season': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'slots': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'time_limit': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'machiavelli.scenario': {
            'Meta': {'object_name': 'Scenario'},
            'cities_to_win': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'start_year': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'title': ('machiavelli.fields.AutoTranslateField', [], {'max_length': '128'})
        }
    }

    complete_apps = ['condottieri_events']
