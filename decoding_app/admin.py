from django.contrib import admin
from .models import Post, SearchQuery

#admin.site.register(Post)
admin.site.register(SearchQuery)
        
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'date_posted', 'date_complete', 'language', 'automatic_punctuation', 'automatic_diarization', 'audio_length', 'audio_file')
    search_fields = ('author__username', 'title', 'language')
    
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    
admin.site.register(Post, PostAdmin)