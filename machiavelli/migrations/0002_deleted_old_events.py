# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'ControlEvent'
        db.delete_table('machiavelli_controlevent')

        # Deleting model 'DisbandEvent'
        db.delete_table('machiavelli_disbandevent')

        # Deleting model 'MovementEvent'
        db.delete_table('machiavelli_movementevent')

        # Deleting model 'ConversionEvent'
        db.delete_table('machiavelli_conversionevent')

        # Deleting model 'OrderEvent'
        db.delete_table('machiavelli_orderevent')

        # Deleting model 'NewUnitEvent'
        db.delete_table('machiavelli_newunitevent')

        # Deleting model 'BaseEvent'
        db.delete_table('machiavelli_baseevent')

        # Deleting model 'StandoffEvent'
        db.delete_table('machiavelli_standoffevent')

        # Deleting model 'CountryEvent'
        db.delete_table('machiavelli_countryevent')

        # Deleting model 'Stats'
        db.delete_table('machiavelli_stats')

        # Deleting model 'UnitEvent'
        db.delete_table('machiavelli_unitevent')


    def backwards(self, orm):
        
        # Adding model 'ControlEvent'
        db.create_table('machiavelli_controlevent', (
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['ControlEvent'])

        # Adding model 'DisbandEvent'
        db.create_table('machiavelli_disbandevent', (
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['DisbandEvent'])

        # Adding model 'MovementEvent'
        db.create_table('machiavelli_movementevent', (
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='origin', to=orm['machiavelli.Area'])),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(related_name='destination', to=orm['machiavelli.Area'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('machiavelli', ['MovementEvent'])

        # Adding model 'ConversionEvent'
        db.create_table('machiavelli_conversionevent', (
            ('before', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('after', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['ConversionEvent'])

        # Adding model 'OrderEvent'
        db.create_table('machiavelli_orderevent', (
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='event_origin', to=orm['machiavelli.Area'])),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('suborigin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='event_suborigin', null=True, to=orm['machiavelli.Area'], blank=True)),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('subconversion', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('conversion', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(related_name='event_destination', null=True, to=orm['machiavelli.Area'], blank=True)),
            ('subtype', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('subcode', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('subdestination', self.gf('django.db.models.fields.related.ForeignKey')(related_name='event_subdestination', null=True, to=orm['machiavelli.Area'], blank=True)),
        ))
        db.send_create_signal('machiavelli', ['OrderEvent'])

        # Adding model 'NewUnitEvent'
        db.create_table('machiavelli_newunitevent', (
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['NewUnitEvent'])

        # Adding model 'BaseEvent'
        db.create_table('machiavelli_baseevent', (
            ('season', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Game'])),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('phase', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('machiavelli', ['BaseEvent'])

        # Adding model 'StandoffEvent'
        db.create_table('machiavelli_standoffevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['StandoffEvent'])

        # Adding model 'CountryEvent'
        db.create_table('machiavelli_countryevent', (
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('message', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('machiavelli', ['CountryEvent'])

        # Adding model 'Stats'
        db.create_table('machiavelli_stats', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('karma', self.gf('django.db.models.fields.PositiveIntegerField')(default=100)),
        ))
        db.send_create_signal('machiavelli', ['Stats'])

        # Adding model 'UnitEvent'
        db.create_table('machiavelli_unitevent', (
            ('message', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['UnitEvent'])


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
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'machiavelli.aftoken': {
            'Meta': {'object_name': 'AFToken'},
            'area': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.Area']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'x': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y': ('django.db.models.fields.PositiveIntegerField', [], {})
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
        'machiavelli.controltoken': {
            'Meta': {'object_name': 'ControlToken'},
            'area': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.Area']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'x': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y': ('django.db.models.fields.PositiveIntegerField', [], {})
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
        'machiavelli.gamearea': {
            'Meta': {'object_name': 'GameArea'},
            'board_area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Player']", 'null': 'True', 'blank': 'True'}),
            'standoff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'})
        },
        'machiavelli.gtoken': {
            'Meta': {'object_name': 'GToken'},
            'area': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.Area']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'x': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'machiavelli.home': {
            'Meta': {'unique_together': "(('scenario', 'country', 'area'),)", 'object_name': 'Home'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Scenario']"})
        },
        'machiavelli.letter': {
            'Meta': {'object_name': 'Letter'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'read': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'receiver': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'received'", 'to': "orm['machiavelli.Player']"}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sent'", 'to': "orm['machiavelli.Player']"})
        },
        'machiavelli.order': {
            'Meta': {'object_name': 'Order'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.GameArea']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'suborder': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.Unit']", 'unique': 'True'})
        },
        'machiavelli.player': {
            'Meta': {'object_name': 'Player'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']", 'null': 'True', 'blank': 'True'}),
            'done': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'machiavelli.retreatorder': {
            'Meta': {'object_name': 'RetreatOrder'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.GameArea']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Unit']"})
        },
        'machiavelli.revolution': {
            'Meta': {'object_name': 'Revolution'},
            'government': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Player']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'opposition': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'machiavelli.scenario': {
            'Meta': {'object_name': 'Scenario'},
            'cities_to_win': ('django.db.models.fields.PositiveIntegerField', [], {'default': '15'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'start_year': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'title': ('machiavelli.fields.AutoTranslateField', [], {'max_length': '128'})
        },
        'machiavelli.score': {
            'Meta': {'object_name': 'Score'},
            'cities': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'machiavelli.setup': {
            'Meta': {'unique_together': "(('scenario', 'area', 'unit_type'),)", 'object_name': 'Setup'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scenario': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Scenario']"}),
            'unit_type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'machiavelli.turnlog': {
            'Meta': {'object_name': 'TurnLog'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log': ('django.db.models.fields.TextField', [], {}),
            'phase': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'season': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'machiavelli.unit': {
            'Meta': {'object_name': 'Unit'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.GameArea']"}),
            'besieging': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'must_retreat': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '5', 'blank': 'True'}),
            'player': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Player']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['machiavelli']
