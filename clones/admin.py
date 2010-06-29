from clones.models import *
from django.contrib import admin

class FingerprintAdmin(admin.ModelAdmin):
	ordering = ['-id']
	list_display = ('__unicode__', 'timestamp')

admin.site.register(Fingerprint, FingerprintAdmin)
admin.site.register(Clone)
