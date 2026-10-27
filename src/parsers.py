from pathlib import Path
import re


def parse_medline(path: str | Path) -> dict[int, str]:
    """Return {document_id: text}, extracting only MEDLINE's .W fields."""
    documents: dict[int, str] = {}
    doc_id: int | None = None
    text_lines: list[str] = []
    in_text = False

    with Path(path).open(encoding="utf-8") as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()
            header = re.fullmatch(r"\.([A-Z])(?:\s+(.*))?", line)

            if header is not None:
                field, value = header.groups()

                if field == "I":
                    if value is None or re.fullmatch(r"[0-9]+", value) is None:
                        raise ValueError(f"Line {line_number}: invalid document ID")
                    next_id = int(value)
                    if next_id < 1:
                        raise ValueError(f"Line {line_number}: document ID must be positive")
                    if next_id == doc_id or next_id in documents:
                        raise ValueError(f"Line {line_number}: duplicate ID {next_id}")

                    # A new document ends the previous one.
                    if doc_id is not None:
                        documents[doc_id] = " ".join(" ".join(text_lines).split())
                    doc_id = next_id
                    text_lines = []

                in_text = field == "W"
                if in_text and doc_id is None:
                    raise ValueError(f"Line {line_number}: .W appears before .I")
            elif in_text:
                text_lines.append(line)

    # Save the last document: no later .I triggers its storage.
    if doc_id is not None:
        documents[doc_id] = " ".join(" ".join(text_lines).split())

    return documents