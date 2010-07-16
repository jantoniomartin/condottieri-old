from django.dispatch import Signal

## unit_placed is sent by Unit when placed
unit_placed = Signal(providing_args=[])
## unit_disbanded is sent by Unit when deleted 
unit_disbanded = Signal(providing_args=[])

## maybe this one could be replaced by a post_save signal
order_placed = Signal(providing_args=["destination", "subtype",
									"suborigin", "subcode", "subdestination",
									"subconversion"])
standoff_happened = Signal(providing_args=[])
unit_converted = Signal(providing_args=["before", "after"])
area_controlled = Signal(providing_args=[])
unit_moved = Signal(providing_args=["destination"])
unit_retreated = Signal(providing_args=["destination"])
support_broken = Signal(providing_args=[])
forced_to_retreat = Signal(providing_args=[])
unit_surrendered = Signal(providing_args=[])
siege_started = Signal(providing_args=[])
government_overthrown = Signal(providing_args=[])
country_conquered = Signal(providing_args=["country"])
