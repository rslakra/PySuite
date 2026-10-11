"""Factory Method — subclasses decide which document type to create."""

from abc import ABC, abstractmethod


class Document(ABC):
    @abstractmethod
    def render(self) -> str: ...


class PDFDocument(Document):
    def render(self) -> str:
        return "%PDF-1.7\n...binary content..."


class HTMLDocument(Document):
    def render(self) -> str:
        return "<html><body><h1>Report</h1></body></html>"


class DocumentCreator(ABC):
    @abstractmethod
    def create_document(self) -> Document: ...

    def export(self) -> str:
        doc = self.create_document()
        return f"Exported {doc.__class__.__name__}:\n{doc.render()}"


class PDFCreator(DocumentCreator):
    def create_document(self) -> Document:
        return PDFDocument()


class HTMLCreator(DocumentCreator):
    def create_document(self) -> Document:
        return HTMLDocument()


def deliver_report(creator: DocumentCreator, label: str) -> None:
    print(f"--- {label} ---")
    print(creator.export())
    print()


def main() -> None:
    deliver_report(PDFCreator(), "PDF pipeline")
    deliver_report(HTMLCreator(), "Web pipeline")


if __name__ == "__main__":
    main()
