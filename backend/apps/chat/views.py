from django.http import StreamingHttpResponse
from rest_framework import generics, permissions, status
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.projects.permissions import ProjectMemberPermission, get_user_project
from apps.rag.graph import iter_research_graph_stream, run_research_graph
from apps.rag.sse import sse_event

from .models import ChatMessage
from .serializers import ChatMessageSerializer


def _chat_event_stream(project_id, user_id, message: str):
    for payload in iter_research_graph_stream(
        project_id=project_id,
        user_id=user_id,
        query=message,
    ):
        event_type = payload.get("type", "message")
        yield sse_event(str(event_type), payload)


class ServerSentEventsRenderer(BaseRenderer):
    """
    DRF content negotiation helper for SSE endpoints.

    Without this, requests with `Accept: text/event-stream` can fail with:
    "Could not satisfy the request Accept header."
    """

    media_type = "text/event-stream"
    format = "sse"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        # This view returns a StreamingHttpResponse; DRF only needs a renderer
        # to accept the `Accept` header during content negotiation.
        return b""


class ChatView(APIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)

    def post(self, request, project_id):
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response(
                {"detail": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)

        result = run_research_graph(
            project_id=str(project.id),
            user_id=request.user.id,
            query=message,
        )
        return Response(
            {
                "answer": result.get("final_answer", ""),
                "citations": result.get("citations", []),
                "message_id": result.get("assistant_message_id"),
                "error": result.get("error"),
            },
            status=status.HTTP_200_OK,
        )


class ChatStreamView(APIView):
    """SSE stream: status → token deltas → done (citations + persisted message id)."""

    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)
    renderer_classes = (ServerSentEventsRenderer,)

    def post(self, request, project_id):
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response(
                {"detail": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        project = get_user_project(request.user, project_id)
        if not project:
            return Response(status=status.HTTP_404_NOT_FOUND)

        response = StreamingHttpResponse(
            _chat_event_stream(str(project.id), request.user.id, message),
            content_type="text/event-stream; charset=utf-8",
        )
        response["Cache-Control"] = "no-cache, no-transform"
        response["X-Accel-Buffering"] = "no"
        return response


class ChatMessageListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated, ProjectMemberPermission)
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.filter(project_id=self.kwargs["project_id"])
