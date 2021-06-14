from django_elasticsearch_dsl import Document, Index, fields
from decoding_app.models import Post
from django_elasticsearch_dsl.registries import registry
from django.contrib.auth import get_user_model

# https://dev.to/aymanemx/building-a-full-text-search-app-using-django-docker-and-elasticsearch-3bai

User = get_user_model()

@registry.register_document
class PostDocument(Document):

    author = fields.ObjectField(properties={
         'username': fields.TextField(),
     })
    
    class Index:
        name = 'posts'
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = Post 

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            'date_posted',
            'language',
            'title',
            'id',
            'slug',
            'transcription',
        ]

        
    def get_queryset(self):
        return super(PostDocument, self).get_queryset().select_related('author')
