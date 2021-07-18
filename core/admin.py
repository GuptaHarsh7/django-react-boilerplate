from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(User)
admin.site.register(Payment)
admin.site.register(Membership)
admin.site.register(File)
admin.site.register(TrackedRequest)
admin.site.register(Address)
