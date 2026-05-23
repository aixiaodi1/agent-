from typing import Protocol


class QueueClient(Protocol):
    def enqueue_ingestion(self, document_id: str, collection: str, app_job_id: str | None = None) -> str: ...
