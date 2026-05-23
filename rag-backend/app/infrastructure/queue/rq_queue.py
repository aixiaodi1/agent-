from redis import Redis
from rq import Queue, Retry


class RqQueueClient:
    def __init__(self, redis_url: str, queue_name: str) -> None:
        self.redis = Redis.from_url(redis_url)
        self.queue = Queue(queue_name, connection=self.redis)

    def enqueue_ingestion(self, document_id: str, collection: str, app_job_id: str | None = None) -> str:
        enqueue_options = {"job_id": app_job_id} if app_job_id is not None else {}
        job = self.queue.enqueue(
            "app.workers.ingest_worker.ingest_document_job",
            document_id,
            collection,
            retry=Retry(max=3, interval=[10, 30, 60]),
            job_timeout="30m",
            failure_ttl=86400,
            **enqueue_options,
        )
        return job.id
