import inspect
import shutil
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from app.config import Settings
from app.errors import ValidationError
from app.infrastructure.queue.base import QueueClient
from app.infrastructure.repositories.base import Repository
from app.services.job_service import JobService


@dataclass(frozen=True)
class _ValidatedUpload:
    filename: str
    extension: str
    content: bytes
    content_type: str
    content_hash: str
    file_size: int


class DocumentService:
    """Upload service.

    File objects are expected to expose ``filename`` and ``read()``. ``read`` may
    be sync or async, matching FastAPI's UploadFile interface.
    """

    def __init__(
        self,
        repository: Repository,
        job_service: JobService,
        queue_client: QueueClient,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.job_service = job_service
        self.queue_client = queue_client
        self.settings = settings

    async def upload_files(self, files: list, collection: str) -> dict:
        normalized_collection = collection.strip()
        if not normalized_collection:
            raise ValidationError("Collection is required.")

        validated_uploads = []
        total_upload_size = 0
        for upload in files:
            content = await self._read_file(upload)
            filename = Path(upload.filename).name
            extension = Path(filename).suffix.lower()
            self._validate_extension(extension)
            file_size = len(content)
            self._validate_size(file_size)
            total_upload_size += file_size
            self._validate_batch_size(total_upload_size)

            validated_uploads.append(
                _ValidatedUpload(
                    filename=filename,
                    extension=extension,
                    content=content,
                    content_type=getattr(upload, "content_type", "") or "application/octet-stream",
                    content_hash=sha256(content).hexdigest(),
                    file_size=file_size,
                )
            )

        documents = []
        jobs = []
        created_document_ids = []
        created_job_ids = []
        saved_upload_dirs = []
        try:
            for upload in validated_uploads:
                placeholder_path = self.settings.upload_dir / "_pending" / upload.filename
                document = self.repository.create_document(
                    filename=upload.filename,
                    collection=normalized_collection,
                    mime_type=upload.content_type,
                    file_size=upload.file_size,
                    source_path=str(placeholder_path),
                    content_hash=upload.content_hash,
                )
                created_document_ids.append(document.id)

                final_path = self.settings.upload_dir / document.id / f"original{upload.extension}"
                saved_upload_dirs.append(final_path.parent)
                final_path.parent.mkdir(parents=True, exist_ok=True)
                final_path.write_bytes(upload.content)
                document = self.repository.update_document_source_path(document.id, str(final_path))

                job = self.job_service.create_job(document.id, normalized_collection)
                created_job_ids.append(job.id)
                job = self.job_service.attach_rq_job(job.id, job.id)
                rq_job = self.queue_client.enqueue_ingestion(
                    document.id,
                    normalized_collection,
                    app_job_id=job.id,
                )
                rq_job_id = getattr(rq_job, "id", rq_job)
                if str(rq_job_id) != job.rq_job_id:
                    job = self.job_service.attach_rq_job(job.id, str(rq_job_id))

                documents.append(document)
                jobs.append(job)
        except Exception as exc:
            error = str(exc)
            self._compensate_batch_best_effort(created_document_ids, created_job_ids, saved_upload_dirs, error)
            raise

        return {"documents": documents, "jobs": jobs}

    async def _read_file(self, upload) -> bytes:
        content = upload.read()
        if inspect.isawaitable(content):
            content = await content
        if not isinstance(content, bytes):
            raise ValidationError("Uploaded file content must be bytes.")
        return content

    def _validate_extension(self, extension: str) -> None:
        if extension not in self.settings.allowed_extensions:
            raise ValidationError(f"Unsupported file extension: {extension}.")

    def _validate_size(self, size_bytes: int) -> None:
        max_bytes = self.settings.max_upload_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValidationError(f"Uploaded file exceeds {self.settings.max_upload_mb} MB.")

    def _validate_batch_size(self, size_bytes: int) -> None:
        max_bytes = self.settings.max_upload_batch_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValidationError(f"Uploaded batch exceeds {self.settings.max_upload_batch_mb} MB.")

    def _compensate_batch_best_effort(
        self,
        document_ids: list[str],
        job_ids: list[str],
        upload_dirs: list[Path],
        error: str,
    ) -> None:
        for document_id in document_ids:
            try:
                self.repository.mark_document_failed(document_id, error)
            except Exception:
                pass

        for job_id in job_ids:
            try:
                self.job_service.mark_failed(job_id, error)
            except Exception:
                pass

        for upload_dir in upload_dirs:
            self._remove_upload_dir_best_effort(upload_dir)

    def _remove_upload_dir_best_effort(self, upload_dir: Path) -> None:
        try:
            upload_root = self.settings.upload_dir.resolve()
            document_dir = upload_dir.resolve()
            if document_dir.parent != upload_root:
                return
            if document_dir.exists():
                shutil.rmtree(document_dir)
        except Exception:
            pass
