#!/usr/bin/env python3
"""Standardize prodoc filenames and export all prodocs as PDFs.

The script leaves source files untouched. It writes standardized PDFs to
``01_Input/08_Prodocs/standardized_pdf`` and writes a CSV manifest describing how
each file was matched to tracker project IDs.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import signal
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PRODOC_ROOT = Path("01_Input/08_Prodocs")
DEFAULT_OUTPUT_ROOT = Path("01_Input/08_Prodocs/standardized_pdf")
DEFAULT_PROJECT_FILES = [
    Path("02_Output/01_Projects/projectDfFull.csv"),
    Path("02_Output/01_Projects/projectDfValidation.csv"),
    Path("02_Output/01_Projects/projectDf.csv"),
]

SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx"}
IGNORED_DIR_NAMES = {"standardized_pdf", "__MACOSX"}
CONVERSION_TIMEOUT_SECONDS = 120
YEAR_LIKE_TOKEN_RE = re.compile(r"^(19|20)\d{2}$")
TOKEN_RE = re.compile(r"[a-z0-9]+")
TITLE_STOPWORDS = {
    "and",
    "annex",
    "clean",
    "cleared",
    "copy",
    "doc",
    "document",
    "docx",
    "english",
    "final",
    "for",
    "full",
    "initiating",
    "initiation",
    "page",
    "pdf",
    "plan",
    "ppm",
    "project",
    "programme",
    "program",
    "prodoc",
    "proposal",
    "revised",
    "signed",
    "the",
    "version",
}
GENERIC_STEM_WORDS = {
    "doc",
    "docx",
    "pdf",
    "prodoc",
    "project document",
    "programme document",
    "program document",
    "signed",
    "final",
}


@dataclass
class ProjectRef:
    project_id: str
    title: str
    funding_source: str | None = None


@dataclass
class ProcessResult:
    source_path: Path
    output_path: Path | None
    ids: list[str]
    match_source: str
    status: str
    notes: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standardize prodoc filenames against project IDs and export PDFs."
    )
    parser.add_argument("--prodoc-root", type=Path, default=DEFAULT_PRODOC_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--project-file",
        action="append",
        type=Path,
        default=[],
        help="Project CSV file with Project ID and Project Title columns. May repeat.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write PDFs. Without this flag, only prints/writes a dry-run manifest.",
    )
    return parser.parse_args()


def normalize_project_id(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    text = text.replace(".0", "") if text.endswith(".0") else text
    if re.fullmatch(r"\d+", text):
        return str(int(text))
    return text


def normalize_funding_source(value: object) -> str | None:
    text = str(value or "").replace("\u00a0", " ").strip()
    text = re.sub(r"\s+", " ", text)
    aliases = {
        "VF": "VF",
        "Vertical Funded": "VF",
        "Vertically Funded": "VF",
        "Non-VF": "Non-VF",
        "non-VF": "Non-VF",
        "NON-VF": "Non-VF",
        "Non VF": "Non-VF",
        "NonVF": "Non-VF",
        "NFV": "Non-VF",
    }
    return aliases.get(text)


def project_id_aliases(project_id: str) -> set[str]:
    aliases = {project_id}
    if project_id.isdigit():
        aliases.add(project_id.zfill(8))
        aliases.add(project_id.zfill(7))
        aliases.add(project_id.zfill(6))
    else:
        aliases.add(compact_alnum(project_id))
        for token, _ in digit_tokens(project_id):
            if not YEAR_LIKE_TOKEN_RE.fullmatch(token):
                aliases.add(token)
                aliases.add(str(int(token)))
    return aliases


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized.lower()


def compact_alnum(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_text(value))


def title_tokens(value: str) -> set[str]:
    normalized = normalize_text(value)
    normalized = re.sub(r"[_\-–—]+", " ", normalized)
    raw_tokens = TOKEN_RE.findall(normalized)
    tokens: set[str] = set()
    for token in raw_tokens:
        token = re.sub(r"^(ppm|prodoc|project|programme|program)+", "", token)
        if len(token) <= 2:
            continue
        if token in TITLE_STOPWORDS:
            continue
        if token.isdigit():
            continue
        tokens.add(token)
    return tokens


def load_projects(project_files: list[Path]) -> tuple[dict[str, ProjectRef], dict[str, str]]:
    projects: dict[str, ProjectRef] = {}
    alias_to_project_id: dict[str, str] = {}
    for path in project_files:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                raw_id = row.get("Project ID") or row.get("projectId") or row.get("id")
                title = row.get("Project Title") or row.get("projectTitle") or row.get("title") or ""
                funding_source = normalize_funding_source(
                    row.get("VF or Non-VF") or row.get("fundingSource")
                )
                for part in re.split(r"[\n,;]+", str(raw_id)):
                    project_id = normalize_project_id(part)
                    if not project_id:
                        continue
                    if project_id not in projects:
                        projects[project_id] = ProjectRef(
                            project_id=project_id,
                            title=title.strip(),
                            funding_source=funding_source,
                        )
                    elif not projects[project_id].funding_source and funding_source:
                        projects[project_id].funding_source = funding_source
                    for alias in project_id_aliases(project_id):
                        alias_to_project_id[alias] = project_id
    return projects, alias_to_project_id


def source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = set(path.relative_to(root).parts)
        if rel_parts & IGNORED_DIR_NAMES:
            continue
        if path.name.startswith("~$") or path.name == ".DS_Store":
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return sorted(files)


def digit_tokens(text: str) -> list[tuple[str, int]]:
    return [(match.group(0), match.start()) for match in re.finditer(r"(?<!\d)\d{4,8}(?!\d)", text)]


def ids_from_text(text: str, alias_to_project_id: dict[str, str]) -> list[str]:
    found: list[tuple[str, int]] = []
    seen = set()
    for token, pos in digit_tokens(text):
        if YEAR_LIKE_TOKEN_RE.fullmatch(token):
            continue
        normalized = str(int(token)) if token.isdigit() else token
        project_id = alias_to_project_id.get(token) or alias_to_project_id.get(normalized)
        if project_id and project_id not in seen:
            found.append((project_id, pos))
            seen.add(project_id)
    compact_text = compact_alnum(text)
    for alias, project_id in alias_to_project_id.items():
        compact_alias = compact_alnum(alias)
        if len(compact_alias) < 6 or not re.search(r"[a-z]", compact_alias):
            continue
        pos = compact_text.find(compact_alias)
        if pos >= 0 and project_id not in seen:
            found.append((project_id, pos))
            seen.add(project_id)
    return [project_id for project_id, _ in sorted(found, key=lambda item: item[1])]


def title_match_ids(queries: list[str], projects: dict[str, ProjectRef]) -> tuple[list[str], str]:
    scored: list[tuple[float, float, str, str]] = []
    for query in queries:
        query_tokens = title_tokens(query)
        if len(query_tokens) < 2:
            continue
        for project_id, project in projects.items():
            project_tokens = title_tokens(project.title)
            if len(project_tokens) < 2:
                continue
            intersection = query_tokens & project_tokens
            if len(intersection) < 2:
                continue
            jaccard = len(intersection) / len(query_tokens | project_tokens)
            project_coverage = len(intersection) / len(project_tokens)
            query_coverage = len(intersection) / len(query_tokens)
            score = max(jaccard, min(project_coverage, query_coverage))
            if score >= 0.50 or (project_coverage >= 0.75 and query_coverage >= 0.30):
                scored.append((score, project_coverage, project_id, project.title))

    if not scored:
        return [], ""

    scored.sort(reverse=True)
    best_score = scored[0][0]
    best = [item for item in scored if best_score - item[0] <= 0.03]
    if len(best) > 1:
        return [item[2] for item in best], "Multiple close project-title matches"
    return [scored[0][2]], f"Matched project title: {scored[0][3]}"


def extract_pdf_text(path: Path) -> str:
    try:
        completed = subprocess.run(
            ["pdftotext", "-enc", "UTF-8", str(path), "-"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=90,
        )
        return completed.stdout or ""
    except Exception:
        return ""


def extract_word_text(path: Path) -> str:
    try:
        completed = subprocess.run(
            ["textutil", "-convert", "txt", "-stdout", str(path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=90,
        )
        return completed.stdout or ""
    except Exception:
        return ""


def extract_document_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    return extract_word_text(path)


def strip_known_ids_from_stem(stem: str, matched_ids: list[str]) -> str:
    cleaned = stem
    cleaned = re.sub(r"\.(docx?|pdf)$", "", cleaned, flags=re.IGNORECASE)
    for project_id in matched_ids:
        for alias in sorted(project_id_aliases(project_id), key=len, reverse=True):
            cleaned = re.sub(rf"(?<!\d){re.escape(alias)}(?!\d)", " ", cleaned)
    cleaned = re.sub(r"\bPIMS\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[_\-–—]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._-")
    return cleaned


def sanitize_filename_part(text: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ._-")
    return cleaned[:150].strip() or "Prodoc"


def sanitize_project_name(text: str) -> str:
    cleaned = sanitize_filename_part(text)
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "Prodoc"


def safe_id_prefix(ids: list[str]) -> str:
    return sanitize_filename_part("+".join(ids)) if ids else "UNMATCHED"


def project_name_for_ids(source: Path, ids: list[str], projects: dict[str, ProjectRef]) -> str:
    titles = [
        projects[project_id].title
        for project_id in ids
        if project_id in projects and projects[project_id].title
    ]
    if not titles:
        return sanitize_project_name(source.stem)
    if len(titles) == 1:
        return sanitize_project_name(titles[0])
    return sanitize_project_name(" + ".join(titles))


def unique_output_path(path: Path) -> Path:
    if not path.exists():
        return path
    base = path.with_suffix("")
    suffix = path.suffix
    for idx in range(2, 1000):
        candidate = Path(f"{base} ({idx}){suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find unique output name for {path}")


def convert_word_to_pdf(source: Path, outdir: Path) -> Path | None:
    outdir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prodoc_convert_") as tmp:
        tmpdir = Path(tmp)
        command = [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(tmpdir),
            str(source),
        ]
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            process.communicate(timeout=CONVERSION_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            return None
        produced = tmpdir / f"{source.stem}.pdf"
        if process.returncode != 0 or not produced.exists():
            return None
        target = outdir / produced.name
        shutil.copy2(produced, target)
        return target


def build_output_path(
    source: Path,
    prodoc_root: Path,
    output_root: Path,
    ids: list[str],
    projects: dict[str, ProjectRef],
) -> Path:
    rel_parent = source.relative_to(prodoc_root).parent
    funding_sources = {
        projects[project_id].funding_source
        for project_id in ids
        if project_id in projects and projects[project_id].funding_source in {"VF", "Non-VF"}
    }
    output_dir = output_root / next(iter(funding_sources)) if len(funding_sources) == 1 else output_root / rel_parent
    id_prefix = safe_id_prefix(ids)
    project_name = project_name_for_ids(source, ids, projects)
    return unique_output_path(output_dir / f"{id_prefix} - {project_name}.pdf")


def copy_or_convert_to_pdf(source: Path, output_path: Path) -> tuple[str, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() == ".pdf":
        shutil.copy2(source, output_path)
        return "copied_pdf", ""
    converted = convert_word_to_pdf(source, output_path.parent)
    if not converted:
        return "conversion_failed", "LibreOffice did not produce a PDF"
    shutil.move(str(converted), str(output_path))
    return "converted_pdf", ""


def process_file(
    source: Path,
    prodoc_root: Path,
    output_root: Path,
    projects: dict[str, ProjectRef],
    alias_to_project_id: dict[str, str],
    apply: bool,
) -> ProcessResult:
    filename_ids = ids_from_text(source.stem, alias_to_project_id)
    ids = filename_ids
    match_source = "filename" if ids else ""
    notes = ""
    if not ids:
        document_text = extract_document_text(source)
        text_ids = ids_from_text(document_text, alias_to_project_id)
        ids = text_ids
        if len(text_ids) == 1:
            match_source = "document_text"
        elif len(text_ids) > 1:
            match_source = "document_text_multiple"
            notes = "Multiple project IDs found in document text"
        else:
            title_ids, title_note = title_match_ids([source.stem, document_text[:2000]], projects)
            ids = title_ids
            if len(title_ids) == 1:
                match_source = "project_title"
                notes = title_note
            elif len(title_ids) > 1:
                match_source = "project_title_multiple"
                notes = title_note
            else:
                match_source = "unmatched"
                notes = "No valid tracker project ID found in filename, extractable document text, or project-title match"
    elif len(ids) > 1:
        match_source = "filename_multiple"
        notes = "Multiple project IDs found in filename"

    output_path = build_output_path(source, prodoc_root, output_root, ids, projects)
    status = "planned"
    if apply:
        status, conversion_note = copy_or_convert_to_pdf(source, output_path)
        notes = "; ".join(part for part in [notes, conversion_note] if part)
    return ProcessResult(
        source_path=source,
        output_path=output_path,
        ids=ids,
        match_source=match_source,
        status=status,
        notes=notes,
    )


def write_manifest(results: list[ProcessResult], output_root: Path, apply: bool) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = output_root / ("prodocs_standardization_manifest.csv" if apply else "prodocs_standardization_manifest_dry_run.csv")
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "status",
                "match_source",
                "project_ids",
                "source_path",
                "output_path",
                "notes",
            ],
        )
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "status": result.status,
                    "match_source": result.match_source,
                    "project_ids": "+".join(result.ids),
                    "source_path": str(result.source_path),
                    "output_path": str(result.output_path) if result.output_path else "",
                    "notes": result.notes,
                }
            )
    return manifest


def main() -> int:
    args = parse_args()
    project_files = args.project_file or DEFAULT_PROJECT_FILES
    projects, alias_to_project_id = load_projects(project_files)
    if not projects:
        raise SystemExit("No project IDs loaded from project files.")

    files = source_files(args.prodoc_root)
    results = [
        process_file(
            source=path,
            prodoc_root=args.prodoc_root,
            output_root=args.output_root,
            projects=projects,
            alias_to_project_id=alias_to_project_id,
            apply=args.apply,
        )
        for path in files
    ]
    manifest = write_manifest(results, args.output_root, args.apply)

    print(f"Mode: {'APPLY' if args.apply else 'DRY RUN'}")
    print(f"Project IDs loaded: {len(projects)}")
    print(f"Source files considered: {len(files)}")
    print(f"Matched from filename: {sum(r.match_source.startswith('filename') for r in results)}")
    print(f"Matched from document text: {sum(r.match_source.startswith('document_text') for r in results)}")
    print(f"Unmatched: {sum(r.match_source == 'unmatched' for r in results)}")
    print(f"Multiple-ID matches: {sum('multiple' in r.match_source for r in results)}")
    if args.apply:
        print(f"PDFs written: {sum(r.status in {'copied_pdf', 'converted_pdf'} for r in results)}")
        print(f"Conversion failures: {sum(r.status == 'conversion_failed' for r in results)}")
    print(f"Manifest: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
