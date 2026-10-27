"""Parse raw IR collections into {document_id: text} dictionaries."""

from pathlib import Path
import re
import warnings


def parse_smart(
    path: str | Path,
    fields: tuple[str, ...] = ("W",),
) -> dict[int, str]:
    """Read SMART records, retaining only the selected fields.

    .I starts a document.
    Selected fields contribute text; other fields are ignored.
    Whitespace is normalized, preserving words, case, and punctuation.
    Empty records retain their IDs with empty text.
    """
    documents: dict[int, str] = {}
    doc_id: int | None = None
    text_lines: list[str] = []
    in_text = False

    with Path(path).open(encoding="utf-8") as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()

            # Examples: ".I 7", ".T", ".W", ".A".
            header = re.fullmatch(r"\.([A-Z])(?:\s+(.*))?", line)

            if header is not None:
                field, value = header.groups()

                if field == "I":
                    if value is None or re.fullmatch(r"[0-9]+", value) is None:
                        raise ValueError(
                            f"Line {line_number}: invalid document ID"
                        )

                    next_id = int(value)

                    if next_id < 1:
                        raise ValueError(
                            f"Line {line_number}: document ID must be positive"
                        )

                    if next_id == doc_id or next_id in documents:
                        raise ValueError(
                            f"Line {line_number}: duplicate ID {next_id}"
                        )

                    # A new document ends the previous one.
                    if doc_id is not None:
                        documents[doc_id] = " ".join(
                            " ".join(text_lines).split()
                        )

                    doc_id = next_id
                    text_lines = []

                in_text = field in fields

                if in_text and doc_id is None:
                    raise ValueError(
                        f"Line {line_number}: .{field} appears before .I"
                    )

            elif in_text:
                text_lines.append(line)

    # Save the final document, which has no following .I.
    if doc_id is not None:
        documents[doc_id] = " ".join(" ".join(text_lines).split())

    return documents


def parse_medline(path: str | Path) -> dict[int, str]:
    """Read MEDLINE, retaining only .W text."""
    return parse_smart(path, fields=("W",))


def parse_cran(path: str | Path) -> dict[int, str]:
    """Read CRAN, retaining .T and .W as required by the handout."""
    return parse_smart(path, fields=("T", "W"))


def parse_cisi(path: str | Path) -> dict[int, str]:
    """Read CISI, retaining .T and .W and ignoring other fields."""
    return parse_smart(path, fields=("T", "W"))


def parse_npl(path: str | Path) -> dict[int, str]:
    """Read records starting with an ID and ending with a / line."""
    documents: dict[int, str] = {}
    doc_id: int | None = None
    text_lines: list[str] = []

    with Path(path).open(encoding="utf-8") as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.strip()

            if not line:
                continue

            if doc_id is None:
                # Expect an ID only when outside a document.
                if re.fullmatch(r"[0-9]+", line) is None or int(line) < 1:
                    raise ValueError(
                        f"Line {line_number}: expected a positive ID"
                    )

                doc_id = int(line)

                if doc_id in documents:
                    raise ValueError(
                        f"Line {line_number}: duplicate ID {doc_id}"
                    )

                text_lines = []

            elif line == "/":
                # A slash on its own ends the document.
                documents[doc_id] = " ".join(" ".join(text_lines).split())
                doc_id = None

            else:
                text_lines.append(line)

    if doc_id is not None:
        raise ValueError(f"Document {doc_id}: missing closing /")

    return documents


def parse_lisa(folder: str | Path) -> dict[int, str]:
    """Read LISA, retaining one copy of each original document ID.

    Identical repeated records are counted once. Conflicting copies raise
    an error. Text outside document boundaries is skipped with a warning.
    """
    paths = sorted(
        path
        for path in Path(folder).iterdir()
        if path.is_file()
        and re.fullmatch(r"LISA\d+\.\d+", path.name, re.I)
    )

    if not paths:
        raise FileNotFoundError(f"No LISA document parts in {folder}")

    documents: dict[int, str] = {}
    duplicate_count = 0
    orphan_count = 0

    for path in paths:
        doc_id: int | None = None
        text_lines: list[str] = []

        with path.open(encoding="utf-8") as source:
            for line_number, raw_line in enumerate(source, start=1):
                line = raw_line.strip()
                location = f"{path.name}:{line_number}"
                header = re.fullmatch(r"Document\s+([0-9]+)", line)

                if header:
                    if doc_id is not None:
                        raise ValueError(
                            f"{location}: missing asterisk separator"
                        )

                    doc_id = int(header[1])

                    if doc_id < 1:
                        raise ValueError(
                            f"{location}: invalid ID {doc_id}"
                        )

                    text_lines = []

                elif line and set(line) == {"*"}:
                    if doc_id is None:
                        continue

                    text = " ".join(" ".join(text_lines).split())

                    if doc_id in documents:
                        # Count identical copies once, but reject conflicts.
                        if documents[doc_id] != text:
                            raise ValueError(
                                f"{location}: conflicting copies of ID {doc_id}"
                            )

                        duplicate_count += 1
                    else:
                        documents[doc_id] = text

                    doc_id = None
                    text_lines = []

                elif line:
                    if doc_id is None:
                        # This text has no document ID to associate it with.
                        orphan_count += 1
                    else:
                        text_lines.append(line)

        if doc_id is not None:
            raise ValueError(
                f"{path.name}: document {doc_id} has no closing separator"
            )

    if duplicate_count or orphan_count:
        warnings.warn(
            f"LISA: ignored {duplicate_count} identical duplicate records "
            f"and {orphan_count} text lines outside document boundaries.",
            UserWarning,
            stacklevel=2,
        )

    return documents