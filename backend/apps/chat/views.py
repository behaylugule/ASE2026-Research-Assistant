import time

from django.http import StreamingHttpResponse
from rest_framework import generics, permissions, status
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.permissions import ProjectMemberPermission, get_user_project
from apps.rag.config import normalize_mode
<<<<<<< HEAD
from apps.rag.pipeline_modes import normalize_pipeline_mode
from apps.rag.pipeline_runner import iter_pipeline_stream, run_pipeline
from apps.rag.pipelines.qa import iter_qa_refine_stream
=======
from apps.rag.graph import iter_research_graph_stream, run_research_graph
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
from apps.rag.sse import sse_event

from .models import ChatMessage, ChatRole
from .serializers import ChatMessageSerializer


<<<<<<< HEAD
def _chat_event_stream(project_id, user_id, message, mode, pipeline_mode, document_id):
    for payload in iter_pipeline_stream(
=======
def _chat_event_stream(project_id, user_id, message: str, mode: str):
    for payload in iter_research_graph_stream(
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
        project_id=project_id,
        user_id=user_id,
        query=message,
        mode=mode,
<<<<<<< HEAD
        pipeline_mode=pipeline_mode,
        document_id=document_id,
    ):
        event_type = payload.get("type", "message")
        yield sse_event(str(event_type), payload)


def _refine_event_stream(project_id, user_id, query, draft, refined_from):
    for payload in iter_qa_refine_stream(
        project_id=project_id,
        user_id=user_id,
        query=query,
        draft_answer=draft,
        refined_from=refined_from,
=======
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
    ):
        event_type = payload.get("type", "message")
        yield sse_event(str(event_type), payload)


class ServerSentEventsRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "sse"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return b""


class ChatView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def post(self, request, project_id):
        message = (request.data.get("message") or "").strip()
        if not message and normalize_pipeline_mode(request.data.get("pipeline_mode")) != "summarize":
            return Response({"detail": "message is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)

        mode = normalize_mode(request.data.get("mode"))
<<<<<<< HEAD
        pipeline_mode = normalize_pipeline_mode(request.data.get("pipeline_mode"))
        document_id = request.data.get("document_id")
        result = run_pipeline(
            project_id=str(project.id),
            user_id=request.user.id,
            query=message or "Summarize document",
            mode=mode,
            pipeline_mode=pipeline_mode,
            document_id=str(document_id) if document_id else None,
=======
        result = run_research_graph(
            project_id=str(project.id),
            user_id=request.user.id,
            query=message,
            mode=mode,
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
        )
        return Response(
            {
                "answer": result.get("final_answer", ""),
                "citations": result.get("citations", []),
                "structured": result.get("structured"),
                "message_id": result.get("assistant_message_id"),
                "error": result.get("error"),
                "mode": mode,
<<<<<<< HEAD
                "pipeline_mode": pipeline_mode,
=======
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
            },
            status=status.HTTP_200_OK,
        )


class ChatStreamView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)
    renderer_classes = (ServerSentEventsRenderer,)

    def post(self, request, project_id):
        message = (request.data.get("message") or "").strip()
        pipeline_mode = normalize_pipeline_mode(request.data.get("pipeline_mode"))
        if not message and pipeline_mode != "summarize":
            return Response({"detail": "message is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)

        mode = normalize_mode(request.data.get("mode"))
<<<<<<< HEAD
        document_id = request.data.get("document_id")
        response = StreamingHttpResponse(
            _chat_event_stream(
                str(project.id),
                request.user.id,
                message or "Summarize document",
                mode,
                pipeline_mode,
                str(document_id) if document_id else None,
            ),
=======
        response = StreamingHttpResponse(
            _chat_event_stream(str(project.id), request.user.id, message, mode),
>>>>>>> 3fe2a911b4c0b85b3a0bf6e7135ee335c854b4db
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response


class ChatRefineStreamView(APIView):
    """Two-phase answer: refine a Fast draft with Deep retrieval + generation."""

    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)
    renderer_classes = (ServerSentEventsRenderer,)

    def post(self, request, project_id):
        assistant_message_id = request.data.get("assistant_message_id")
        if not assistant_message_id:
            return Response({"detail": "assistant_message_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            assistant = ChatMessage.objects.get(
                pk=assistant_message_id,
                project_id=project_id,
                role=ChatRole.ASSISTANT,
            )
        except ChatMessage.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        user_msg = (
            ChatMessage.objects.filter(
                project_id=project_id,
                role=ChatRole.USER,
                created_at__lt=assistant.created_at,
            )
            .order_by("-created_at")
            .first()
        )
        if not user_msg:
            return Response({"detail": "No user message found for refinement"}, status=status.HTTP_400_BAD_REQUEST)

        response = StreamingHttpResponse(
            _refine_event_stream(
                str(project.id),
                request.user.id,
                user_msg.content,
                assistant.content,
                str(assistant.id),
            ),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response


class ChatBenchmarkView(APIView):
    """Compare Fast vs Deep for the same query (demo / evaluation)."""

    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def post(self, request, project_id):
        query = (request.data.get("query") or "").strip()
        if not query:
            return Response({"detail": "query is required"}, status=status.HTTP_400_BAD_REQUEST)
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)

        pipeline_mode = normalize_pipeline_mode(request.data.get("pipeline_mode"))
        document_id = request.data.get("document_id")
        results: dict[str, dict] = {}
        for mode in ("fast", "deep"):
            started = time.perf_counter()
            result = run_pipeline(
                project_id=str(project.id),
                user_id=request.user.id,
                query=query,
                mode=mode,
                pipeline_mode=pipeline_mode,
                document_id=str(document_id) if document_id else None,
            )
            total_ms = round((time.perf_counter() - started) * 1000, 1)
            results[mode] = {
                "answer": result.get("final_answer", ""),
                "citations": result.get("citations", []),
                "citations_count": len(result.get("citations") or []),
                "latency_ms": total_ms,
                "error": result.get("error"),
            }
        return Response({"query": query, "pipeline_mode": pipeline_mode, "results": results})


class ChatMessageListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.filter(project_id=self.kwargs["project_id"])
