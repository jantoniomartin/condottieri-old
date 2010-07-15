# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
    def forwards(self, orm):
        for event in orm['machiavelli.BaseEvent'].objects.all():
			try:
				event.newunitevent
			except:
				pass
			else:
				e = orm.NewUnitEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													country=event.country,
													type=event.type,
													area=event.area)
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.disbandevent
			except:
				pass
			else:
				e = orm.DisbandEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													country=event.country,
													type=event.type,
													area=event.area)
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.orderevent
			except:
				pass
			else:
				e = orm.DisbandEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													country=event.country,
													type=event.type,
													origin=event.origin,
													code=event.code,
													destination=event.destination)
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.standoffevent
			except:
				pass
			else:
				e = orm.StandoffEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													area=event.area)
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.conversionevent
			except:
				pass
			else:
				e = orm.ConversionEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													area=event.area,
													before=event.before,
													after=event.after)
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.controlevent
			except:
				pass
			else:
				e = orm.ControlEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													country=event.country,
													area=event.area)
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.movementevent
			except:
				pass
			else:
				if event.phase == 2:
					e = orm.MovementEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													type=event.type,
													origin=event.origin,
													destination=event.destination)
				elif event.phase == 3:
					e = orm.RetreatEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													type=event.type,
													origin=event.origin,
													destination=event.destination)
				else:
					print "Odd, event phase not 2 or 3"
					continue
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.unitevent
			except:
				pass
			else:
				e = orm.UnitEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													type=event.type,
													area=event.area,
													message=event.message)
				e.save()
				print "Saved event %s" % e
				continue
			try:
				event.countryevent
			except:
				print "Error: event %s has no child" % event
			else:
				e = orm.CountryEvent.objects.create(game=event.game,
													year=event.year,
													season=event.season,
													phase=event.phase,
													country=event.country,
													message=event.message)
				e.save()
				print "Saved event %s" % e

    def backwards(self, orm):
		raise RuntimeError("Cannot reverse this migration")

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
            'game': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_baseevent'", 'to': "orm['machiavelli.Game']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'phase': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'season': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'year': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'machiavelli.controlevent': {
            'Meta': {'object_name': 'ControlEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_controlevent'", 'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_controlevent'", 'to': "orm['machiavelli.Country']"})
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
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_conversionevent'", 'to': "orm['machiavelli.Area']"}),
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
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_countryevent'", 'to': "orm['machiavelli.Country']"}),
            'message': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'machiavelli.disbandevent': {
            'Meta': {'object_name': 'DisbandEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_disbandevent'", 'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'old_disbandevent'", 'null': 'True', 'to': "orm['machiavelli.Country']"}),
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
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_movementevent_destination'", 'to': "orm['machiavelli.Area']"}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_movementevent_origin'", 'to': "orm['machiavelli.Area']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        },
        'machiavelli.newunitevent': {
            'Meta': {'object_name': 'NewUnitEvent', '_ormbases': ['machiavelli.BaseEvent']},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_newunitevent'", 'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_newunitevent'", 'to': "orm['machiavelli.Country']"}),
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
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_orderevent'", 'to': "orm['machiavelli.Country']"}),
            'destination': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'old_orderevent_destination'", 'null': 'True', 'to': "orm['machiavelli.Area']"}),
            'origin': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_orderevent_origin'", 'to': "orm['machiavelli.Area']"}),
            'subcode': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'subconversion': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'subdestination': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'old_orderevent_subdestination'", 'null': 'True', 'to': "orm['machiavelli.Area']"}),
            'suborigin': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'old_orderevent_suborigin'", 'null': 'True', 'to': "orm['machiavelli.Area']"}),
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
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_standoffevent'", 'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'})
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
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'old_unitevent'", 'to': "orm['machiavelli.Area']"}),
            'baseevent_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['machiavelli.BaseEvent']", 'unique': 'True', 'primary_key': 'True'}),
            'message': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['machiavelli', 'condottieri_events']
