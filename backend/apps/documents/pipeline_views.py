from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document, SummaryStatus
from apps.documents.tasks import summarize_document
from apps.projects.permissions import ProjectMemberPermission, get_user_project
from apps.rag.pipeline_runner import run_pipeline


class DocumentSummarizeView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def post(self, request, project_id, pk):
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        doc = Document.objects.filter(project=project, pk=pk).first()
        if not doc:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if doc.status != "ready":
            return Response(
                {"detail": "Document must be indexed (ready) before summarization"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        doc.summary_status = SummaryStatus.PROCESSING
        doc.save(update_fields=["summary_status", "updated_at"])
        summarize_document.delay(str(doc.id))
        return Response(
            {"document_id": str(doc.id), "summary_status": doc.summary_status},
            status=status.HTTP_202_ACCEPTED,
        )


class DocumentSummaryView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def get(self, request, project_id, pk):
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        doc = Document.objects.filter(project=project, pk=pk).first()
        if not doc:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "document_id": str(doc.id),
                "document_name": doc.original_filename,
                "summary_status": doc.summary_status,
                "summary_updated_at": doc.summary_updated_at,
                "summary": doc.summary_json,
            }
        )


class LiteratureSearchView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def post(self, request, project_id):
        query = (request.data.get("query") or request.data.get("message") or "").strip()
        if not query:
            return Response({"detail": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        from apps.rag.config import normalize_mode

        mode = normalize_mode(request.data.get("mode"))
        result = run_pipeline(
            project_id=str(project.id),
            user_id=request.user.id,
            query=query,
            mode=mode,
            pipeline_mode="literature_search",
        )
        return Response(
            {
                "answer": result.get("final_answer", ""),
                "citations": result.get("citations", []),
                "structured": result.get("structured"),
                "pipeline_mode": "literature_search",
            }
        )


class SynthesisView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def post(self, request, project_id):
        query = (request.data.get("query") or request.data.get("message") or "").strip()
        if not query:
            return Response({"detail": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)
        from apps.rag.config import normalize_mode

        mode = normalize_mode(request.data.get("mode", "deep"))
        result = run_pipeline(
            project_id=str(project.id),
            user_id=request.user.id,
            query=query,
            mode=mode,
            pipeline_mode="synthesis",
        )
        return Response(
            {
                "answer": result.get("final_answer", ""),
                "citations": result.get("citations", []),
                "pipeline_mode": "synthesis",
            }
        )
