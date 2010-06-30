# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Scenario'
        db.create_table('machiavelli_scenario', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=16)),
            ('title', self.gf('machiavelli.fields.AutoTranslateField')(max_length=128)),
            ('start_year', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('cities_to_win', self.gf('django.db.models.fields.PositiveIntegerField')(default=15)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Scenario'])

        # Adding model 'Country'
        db.create_table('machiavelli_country', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('machiavelli.fields.AutoTranslateField')(unique=True, max_length=20)),
            ('css_class', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
        ))
        db.send_create_signal('machiavelli', ['Country'])

        # Adding model 'Area'
        db.create_table('machiavelli_area', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('machiavelli.fields.AutoTranslateField')(unique=True, max_length=25)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=5)),
            ('is_sea', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_coast', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('has_city', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('is_fortified', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('has_port', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Area'])

        # Adding M2M table for field borders on 'Area'
        db.create_table('machiavelli_area_borders', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_area', models.ForeignKey(orm['machiavelli.area'], null=False)),
            ('to_area', models.ForeignKey(orm['machiavelli.area'], null=False))
        ))
        db.create_unique('machiavelli_area_borders', ['from_area_id', 'to_area_id'])

        # Adding model 'Home'
        db.create_table('machiavelli_home', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Scenario'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['Home'])

        # Adding unique constraint on 'Home', fields ['scenario', 'country', 'area']
        db.create_unique('machiavelli_home', ['scenario_id', 'country_id', 'area_id'])

        # Adding model 'Setup'
        db.create_table('machiavelli_setup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Scenario'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'], null=True, blank=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
            ('unit_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('machiavelli', ['Setup'])

        # Adding unique constraint on 'Setup', fields ['scenario', 'area', 'unit_type']
        db.create_unique('machiavelli_setup', ['scenario_id', 'area_id', 'unit_type'])

        # Adding model 'Game'
        db.create_table('machiavelli_game', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=20, db_index=True)),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('season', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('phase', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, null=True, blank=True)),
            ('slots', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('scenario', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Scenario'])),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('map_outdated', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('time_limit', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('last_phase_change', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Game'])

        # Adding model 'GameArea'
        db.create_table('machiavelli_gamearea', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Game'])),
            ('board_area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
            ('player', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Player'], null=True, blank=True)),
            ('standoff', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['GameArea'])

        # Adding model 'Stats'
        db.create_table('machiavelli_stats', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('karma', self.gf('django.db.models.fields.PositiveIntegerField')(default=100)),
        ))
        db.send_create_signal('machiavelli', ['Stats'])

        # Adding model 'Score'
        db.create_table('machiavelli_score', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Game'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('points', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('cities', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
        ))
        db.send_create_signal('machiavelli', ['Score'])

        # Adding model 'Player'
        db.create_table('machiavelli_player', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Game'])),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'], null=True, blank=True)),
            ('done', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Player'])

        # Adding model 'Revolution'
        db.create_table('machiavelli_revolution', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('government', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Player'])),
            ('opposition', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], null=True, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Revolution'])

        # Adding model 'Unit'
        db.create_table('machiavelli_unit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.GameArea'])),
            ('player', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Player'])),
            ('besieging', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('must_retreat', self.gf('django.db.models.fields.CharField')(default='', max_length=5, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Unit'])

        # Adding model 'Order'
        db.create_table('machiavelli_order', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.Unit'], unique=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.GameArea'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('suborder', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Order'])

        # Adding model 'RetreatOrder'
        db.create_table('machiavelli_retreatorder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Unit'])),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.GameArea'], null=True, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['RetreatOrder'])

        # Adding model 'ControlToken'
        db.create_table('machiavelli_controltoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.Area'], unique=True)),
            ('x', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('y', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('machiavelli', ['ControlToken'])

        # Adding model 'GToken'
        db.create_table('machiavelli_gtoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.Area'], unique=True)),
            ('x', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('y', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('machiavelli', ['GToken'])

        # Adding model 'AFToken'
        db.create_table('machiavelli_aftoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.Area'], unique=True)),
            ('x', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('y', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('machiavelli', ['AFToken'])

        # Adding model 'BaseEvent'
        db.create_table('machiavelli_baseevent', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Game'])),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('season', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('phase', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('machiavelli', ['BaseEvent'])

        # Adding model 'NewUnitEvent'
        db.create_table('machiavelli_newunitevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['NewUnitEvent'])

        # Adding model 'DisbandEvent'
        db.create_table('machiavelli_disbandevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'], null=True, blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['DisbandEvent'])

        # Adding model 'OrderEvent'
        db.create_table('machiavelli_orderevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
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
        db.send_create_signal('machiavelli', ['OrderEvent'])

        # Adding model 'StandoffEvent'
        db.create_table('machiavelli_standoffevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['StandoffEvent'])

        # Adding model 'ConversionEvent'
        db.create_table('machiavelli_conversionevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
            ('before', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('after', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('machiavelli', ['ConversionEvent'])

        # Adding model 'ControlEvent'
        db.create_table('machiavelli_controlevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['ControlEvent'])

        # Adding model 'MovementEvent'
        db.create_table('machiavelli_movementevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('origin', self.gf('django.db.models.fields.related.ForeignKey')(related_name='origin', to=orm['machiavelli.Area'])),
            ('destination', self.gf('django.db.models.fields.related.ForeignKey')(related_name='destination', to=orm['machiavelli.Area'])),
        ))
        db.send_create_signal('machiavelli', ['MovementEvent'])

        # Adding model 'UnitEvent'
        db.create_table('machiavelli_unitevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Area'])),
            ('message', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('machiavelli', ['UnitEvent'])

        # Adding model 'CountryEvent'
        db.create_table('machiavelli_countryevent', (
            ('baseevent_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['machiavelli.BaseEvent'], unique=True, primary_key=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Country'])),
            ('message', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('machiavelli', ['CountryEvent'])

        # Adding model 'Letter'
        db.create_table('machiavelli_letter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(related_name='sent', to=orm['machiavelli.Player'])),
            ('receiver', self.gf('django.db.models.fields.related.ForeignKey')(related_name='received', to=orm['machiavelli.Player'])),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('read', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
        ))
        db.send_create_signal('machiavelli', ['Letter'])

        # Adding model 'TurnLog'
        db.create_table('machiavelli_turnlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['machiavelli.Game'])),
            ('year', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('season', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('phase', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('log', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('machiavelli', ['TurnLog'])


    def backwards(self, orm):
        
        # Deleting model 'Scenario'
        db.delete_table('machiavelli_scenario')

        # Deleting model 'Country'
        db.delete_table('machiavelli_country')

        # Deleting model 'Area'
        db.delete_table('machiavelli_area')

        # Removing M2M table for field borders on 'Area'
        db.delete_table('machiavelli_area_borders')

        # Deleting model 'Home'
        db.delete_table('machiavelli_home')

        # Removing unique constraint on 'Home', fields ['scenario', 'country', 'area']
        db.delete_unique('machiavelli_home', ['scenario_id', 'country_id', 'area_id'])

        # Deleting model 'Setup'
        db.delete_table('machiavelli_setup')

        # Removing unique constraint on 'Setup', fields ['scenario', 'area', 'unit_type']
        db.delete_unique('machiavelli_setup', ['scenario_id', 'area_id', 'unit_type'])

        # Deleting model 'Game'
        db.delete_table('machiavelli_game')

        # Deleting model 'GameArea'
        db.delete_table('machiavelli_gamearea')

        # Deleting model 'Stats'
        db.delete_table('machiavelli_stats')

        # Deleting model 'Score'
        db.delete_table('machiavelli_score')

        # Deleting model 'Player'
        db.delete_table('machiavelli_player')

        # Deleting model 'Revolution'
        db.delete_table('machiavelli_revolution')

        # Deleting model 'Unit'
        db.delete_table('machiavelli_unit')

        # Deleting model 'Order'
        db.delete_table('machiavelli_order')

        # Deleting model 'RetreatOrder'
        db.delete_table('machiavelli_retreatorder')

        # Deleting model 'ControlToken'
        db.delete_table('machiavelli_controltoken')

        # Deleting model 'GToken'
        db.delete_table('machiavelli_gtoken')

        # Deleting model 'AFToken'
        db.delete_table('machiavelli_aftoken')

        # Deleting model 'BaseEvent'
        db.delete_table('machiavelli_baseevent')

        # Deleting model 'NewUnitEvent'
        db.delete_table('machiavelli_newunitevent')

        # Deleting model 'DisbandEvent'
        db.delete_table('machiavelli_disbandevent')

        # Deleting model 'OrderEvent'
        db.delete_table('machiavelli_orderevent')

        # Deleting model 'StandoffEvent'
        db.delete_table('machiavelli_standoffevent')

        # Deleting model 'ConversionEvent'
        db.delete_table('machiavelli_conversionevent')

        # Deleting model 'ControlEvent'
        db.delete_table('machiavelli_controlevent')

        # Deleting model 'MovementEvent'
        db.delete_table('machiavelli_movementevent')

        # Deleting model 'UnitEvent'
        db.delete_table('machiavelli_unitevent')

        # Deleting model 'CountryEvent'
        db.delete_table('machiavelli_countryevent')

        # Deleting model 'Letter'
        db.delete_table('machiavelli_letter')

        # Deleting model 'TurnLog'
        db.delete_table('machiavelli_turnlog')


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
        'machiavelli.baseevent': {
            'Meta': {'object_name': 'BaseEvent'},
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phase': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'season': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'machiavelli.controlevent': {
            'Meta': {'object_name': 'ControlEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"})
        },
        'machiavelli.controltoken': {
            'Meta': {'object_name': 'ControlToken'},
            'area': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.Area']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'x': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'y': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'machiavelli.conversionevent': {
            'Meta': {'object_name': 'ConversionEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'after': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'before': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'machiavelli.country': {
            'Meta': {'object_name': 'Country'},
            'css_class': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('machiavelli.fields.AutoTranslateField', [], {'unique': 'True', 'max_length': '20'})
        },
        'machiavelli.countryevent': {
            'Meta': {'object_name': 'CountryEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"}),
            'message': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'machiavelli.disbandevent': {
            'Meta': {'object_name': 'DisbandEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
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
        'machiavelli.movementevent': {
            'Meta': {'object_name': 'MovementEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'destination'", 'to': "orm['machiavelli.Area']"}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'origin'", 'to': "orm['machiavelli.Area']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'machiavelli.newunitevent': {
            'Meta': {'object_name': 'NewUnitEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Country']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
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
        'machiavelli.orderevent': {
            'Meta': {'object_name': 'OrderEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
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
        'machiavelli.standoffevent': {
            'Meta': {'object_name': 'StandoffEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'})
        },
        'machiavelli.stats': {
            'Meta': {'object_name': 'Stats'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'karma': ('django.db.models.fields.PositiveIntegerField', [], {'default': '100'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
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
        },
        'machiavelli.unitevent': {
            'Meta': {'object_name': 'UnitEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'message': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['machiavelli']
