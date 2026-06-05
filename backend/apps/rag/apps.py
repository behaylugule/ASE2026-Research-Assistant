import logging
import os
import sys
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class RagConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.rag"
    label = "rag"

    def ready(self) -> None:
        # Avoid loading the model in runserver's autoreload parent (loads twice, blocks startup).
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return

        def _warm() -> None:
            try:
                from apps.rag.services.embeddings import warm_embedding_model

                warm_embedding_model()
                logger.info("Embedding model warmed up")
            except Exception as exc:
                logger.warning("Could not warm embedding model: %s", exc)

        threading.Thread(target=_warm, daemon=True, name="embed-warmup").start()
