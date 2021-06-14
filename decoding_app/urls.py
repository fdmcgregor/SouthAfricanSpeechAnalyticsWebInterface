from django.urls import path, re_path
from .views import (HomeView, PostDetailView,
                    PostDeleteView, UserPostListView,
                    FileView)
from . import views

urlpatterns = [
    path('', HomeView.as_view(), name='decoding-app-home'),
    path('', HomeView.as_view(), name='home'),
    path('user/<str:username>', UserPostListView.as_view(), name='user-posts'),
    path('post/new/', views.post_create_view, name='post-create'),
    path('post/<slug:slug>/delete', PostDeleteView.as_view(), name='post-delete'),
    path('about/', views.about, name='decoding-app-about'),
    path('verify/', views.verify_and_upload, name='verify'),
    path('contact/', views.contact, name='contact'),
    path('account/', views.account, name='account'),
    path('expired/', views.expired, name='expired'),
    path('search/', views.global_search, name='global-search'),
    path('post/<slug:slug>/download/<str:file_type>', FileView.as_view(), name='file-download'),
    path('post/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
    path('jobcomplete/', views.jobcomplete, name='jobcomplete'),
]
