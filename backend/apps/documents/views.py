from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count

from apps.projects.permissions import ProjectMemberPermission, get_user_project
from apps.rag.models import DocumentChunk

from .models import Document, DocumentStatus
from .serializers import DocumentCreateSerializer, DocumentSerializer
from .tasks import ingest_document


class DocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DocumentCreateSerializer
        return DocumentSerializer

    def get_project(self):
        return get_user_project(self.request.user, self.kwargs["project_id"])

    def get_queryset(self):
        return (
            Document.objects.filter(project_id=self.kwargs["project_id"])
            .annotate(chunk_count=Count("chunks"))
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["project"] = self.get_project()
        return ctx

    def perform_create(self, serializer):
        serializer.save()
        doc = serializer.instance
        ingest_document.delay(str(doc.id))


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)
    serializer_class = DocumentSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return (
            Document.objects.filter(project_id=self.kwargs["project_id"])
            .annotate(chunk_count=Count("chunks"))
        )


class DocumentRetryView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def post(self, request, project_id, pk):
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            doc = Document.objects.get(pk=pk, project_id=project_id)
        except Document.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if doc.status not in (DocumentStatus.FAILED, DocumentStatus.PENDING):
            return Response(
                {"detail": "Only failed or pending documents can be retried."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        doc.status = DocumentStatus.PENDING
        doc.error_message = ""
        doc.ingestion_progress = 0
        doc.ingestion_stage = "queued"
        doc.save(update_fields=["status", "error_message", "ingestion_progress", "ingestion_stage", "updated_at"])
        ingest_document.delay(str(doc.id))
        doc = Document.objects.annotate(chunk_count=Count("chunks")).get(pk=doc.pk)
        return Response(DocumentSerializer(doc).data)


class DocumentChunkDetailView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def get(self, request, project_id, chunk_id):
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            chunk = DocumentChunk.objects.select_related("document").get(
                pk=chunk_id,
                document__project_id=project_id,
            )
        except DocumentChunk.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        meta = chunk.metadata or {}
        return Response(
            {
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "document_name": meta.get("document_name") or chunk.document.original_filename,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "token_count": chunk.token_count,
            }
        )
