from django.contrib import admin
from .models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_seconds')
    search_fields = ('user__username',)
    
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    
admin.site.register(Profile, ProfileAdmin)

