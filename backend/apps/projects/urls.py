from django.urls import path

from apps.chat.views import (
    ChatBenchmarkView,
    ChatMessageListView,
    ChatRefineStreamView,
    ChatStreamView,
    ChatView,
)
from apps.documents.pipeline_views import (
    DocumentSummarizeView,
    DocumentSummaryView,
    LiteratureSearchView,
    SynthesisView,
)
from apps.documents.views import (
    DocumentChunkDetailView,
    DocumentDetailView,
    DocumentListCreateView,
    DocumentRetryView,
)

from .views import ProjectDetailView, ProjectListCreateView

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="project-list"),
    path("projects/<uuid:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<uuid:project_id>/documents/",
        DocumentListCreateView.as_view(),
        name="document-list",
    ),
    path(
        "projects/<uuid:project_id>/documents/<uuid:pk>/",
        DocumentDetailView.as_view(),
        name="document-detail",
    ),
    path(
        "projects/<uuid:project_id>/documents/<uuid:pk>/retry/",
        DocumentRetryView.as_view(),
        name="document-retry",
    ),
    path(
        "projects/<uuid:project_id>/chunks/<uuid:chunk_id>/",
        DocumentChunkDetailView.as_view(),
        name="document-chunk-detail",
    ),
    path(
        "projects/<uuid:project_id>/documents/<uuid:pk>/summarize/",
        DocumentSummarizeView.as_view(),
        name="document-summarize",
    ),
    path(
        "projects/<uuid:project_id>/documents/<uuid:pk>/summary/",
        DocumentSummaryView.as_view(),
        name="document-summary",
    ),
    path(
        "projects/<uuid:project_id>/literature-search/",
        LiteratureSearchView.as_view(),
        name="literature-search",
    ),
    path(
        "projects/<uuid:project_id>/synthesis/",
        SynthesisView.as_view(),
        name="synthesis",
    ),
    path(
        "projects/<uuid:project_id>/chat/",
        ChatView.as_view(),
        name="project-chat",
    ),
    path(
        "projects/<uuid:project_id>/chat/stream/",
        ChatStreamView.as_view(),
        name="project-chat-stream",
    ),
    path(
        "projects/<uuid:project_id>/chat/refine/stream/",
        ChatRefineStreamView.as_view(),
        name="project-chat-refine-stream",
    ),
    path(
        "projects/<uuid:project_id>/chat/benchmark/",
        ChatBenchmarkView.as_view(),
        name="project-chat-benchmark",
    ),
    path(
        "projects/<uuid:project_id>/chat/messages/",
        ChatMessageListView.as_view(),
        name="chat-messages",
    ),
]
