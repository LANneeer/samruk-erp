from pathlib import Path
from uuid import UUID

from src.dto.commands import CreateDocument, UpdateDocument, DeleteDocument
from src.infrastructure.unit_of_work import InMemoryUnitOfWork
from src.bootstrap.settings import bootstrap


class PrintNotifier:
    def send(self, *, channel: str, message: str) -> None:
        print(f"[NOTIFY:{channel}] {message}")


class PrintPublisher:
    def publish(self, topic: str, payload: dict) -> None:
        print(f"[PUBLISH:{topic}] {payload}")


def main() -> None:
    uow = InMemoryUnitOfWork()
    bus = bootstrap(uow, notifier=PrintNotifier(), publisher=PrintPublisher())

    sample_path = "data/documents/sample.txt"
    # make sure sample file exists (this is a demo scenario)
    Path(sample_path).parent.mkdir(parents=True, exist_ok=True)
    Path(sample_path).write_bytes(b"Sample file contents")

    [doc_id] = bus.handle(CreateDocument(title="My Document", file_name=sample_path, author_id=UUID("12345678-1234-5678-9012-123456789012")))
    assert isinstance(doc_id, UUID)

    bus.handle(UpdateDocument(document_id=doc_id, title="Updated Title"))

    document = uow.documents.get(doc_id)
    print("Document state:", document.title, document.file_name)

    bus.handle(DeleteDocument(document_id=doc_id))
    print("Document deleted")


if __name__ == "__main__":
    main()