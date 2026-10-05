
from django.contrib import admin
from .models import Game, GamerProfile, LibraryEntry

admin.site.register(Game)
admin.site.register(GamerProfile)
admin.site.register(LibraryEntry)