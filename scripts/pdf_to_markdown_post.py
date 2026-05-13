#!/usr/bin/env python3
"""Convert a PDF into a deterministic Jekyll Markdown post.

The script uses Poppler's pdftotext for readable text extraction and
pdfimages for deterministic image extraction. It intentionally does not use
an LLM.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PdfImageEntry:
    page: int
    image_type: str


@dataclass(frozen=True)
class PdfImage:
    index: int
    page: int
    source: Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required command: {name}")


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "post"


def yaml_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def clean_pdf_stem(stem: str) -> str:
    stem = re.sub(r"^_[0-9a-fA-F]{8,}-", "", stem)
    stem = re.sub(r"-\d{6,}-\d{6,}(?:\s*\(\d+\))?$", "", stem)
    stem = re.sub(r"\s*\(\d+\)$", "", stem)
    return stem.replace("_", " ").replace("-", " ").strip()


def title_from_pdf_stem(pdf: Path) -> str:
    words = clean_pdf_stem(pdf.stem)
    return re.sub(r"\s+", " ", words).strip().title() or "Untitled"


def extract_text_pages(pdf: Path) -> list[str]:
    result = run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), "-"])
    return result.stdout.split("\f")


def list_image_entries(pdf: Path) -> list[PdfImageEntry]:
    result = run(["pdfimages", "-list", str(pdf)])
    entries: list[PdfImageEntry] = []
    for line in result.stdout.splitlines():
        if not re.match(r"^\s*\d+\s+\d+\s+", line):
            continue
        parts = line.split()
        entries.append(PdfImageEntry(page=int(parts[0]), image_type=parts[2]))
    return entries


def extract_images(pdf: Path, temp_dir: Path, slug: str) -> list[Path]:
    prefix = temp_dir / slug
    run(["pdfimages", "-png", str(pdf), str(prefix)])
    return sorted(temp_dir.glob(f"{slug}-*"))


def copy_images(
    extracted_images: list[Path],
    image_entries: list[PdfImageEntry],
    asset_dir: Path,
    public_asset_dir: str,
    slug: str,
    force: bool,
) -> tuple[list[PdfImage], dict[Path, str]]:
    if len(extracted_images) != len(image_entries):
        raise SystemExit(
            "Extracted image count did not match pdfimages -list output: "
            f"{len(extracted_images)} extracted vs {len(image_entries)} listed"
        )

    asset_dir.mkdir(parents=True, exist_ok=True)
    images: list[PdfImage] = []
    public_paths: dict[Path, str] = {}

    for source, entry in zip(extracted_images, image_entries):
        if entry.image_type != "image":
            continue

        index = len(images)
        extension = source.suffix.lower() or ".png"
        destination = asset_dir / f"{slug}-{index:03d}{extension}"
        if destination.exists() and not force:
            raise SystemExit(f"Refusing to overwrite existing image: {destination}")
        shutil.copyfile(source, destination)
        image = PdfImage(index=index, page=entry.page, source=destination)
        images.append(image)
        public_paths[destination] = f"{public_asset_dir.rstrip('/')}/{slug}/{destination.name}"

    return images, public_paths


def looks_like_heading(text: str) -> bool:
    if len(text) > 80:
        return False
    if text.endswith((".", ",", ":", ";", "?", "!", ")")):
        return False
    if re.match(r"^[-*]\s+", text):
        return False
    if re.match(r"^\d+[.)]\s+", text):
        return False
    words = text.split()
    if not words or len(words) > 8:
        return False
    lowercase_words = sum(1 for word in words if word[:1].islower())
    return lowercase_words == 0 or len(words) <= 3


def flush_paragraph(output: list[str], paragraph: list[str]) -> None:
    if not paragraph:
        return
    output.append(" ".join(paragraph))
    output.append("")
    paragraph.clear()


def convert_text_page(page_text: str, page_number: int, title: str) -> list[str]:
    output: list[str] = [f"<!-- Page {page_number} -->", ""]
    paragraph: list[str] = []
    skipped_title = False

    raw_lines = [line.rstrip() for line in page_text.splitlines()]
    while raw_lines and not raw_lines[0].strip():
        raw_lines.pop(0)
    while raw_lines and not raw_lines[-1].strip():
        raw_lines.pop()

    for raw_line in raw_lines:
        text = re.sub(r"[ \t]+", " ", raw_line.strip())

        if not text:
            flush_paragraph(output, paragraph)
            continue

        if page_number == 1 and not skipped_title and text == title:
            skipped_title = True
            continue

        if looks_like_heading(text):
            flush_paragraph(output, paragraph)
            output.append(f"## {text}")
            output.append("")
            continue

        if re.match(r"^[*•]\s+", text):
            flush_paragraph(output, paragraph)
            output.append("- " + re.sub(r"^[*•]\s+", "", text))
            continue

        if re.match(r"^\d+[.)]\s+", text):
            flush_paragraph(output, paragraph)
            output.append(re.sub(r"^(\d+)[.)]\s+", r"\1. ", text))
            continue

        paragraph.append(text)

    flush_paragraph(output, paragraph)
    return output


def image_markdown(
    page_images: list[PdfImage],
    public_paths: dict[Path, str],
    title: str,
) -> list[str]:
    if not page_images:
        return []

    output = ["<!-- Images extracted from this PDF page -->", ""]
    for image in page_images:
        public_path = public_paths[image.source]
        output.append(
            f"![Image {image.index + 1} from {title}, page {image.page}]({public_path})"
        )
        output.append("")
    return output


def build_markdown(
    title: str,
    date: str,
    categories: str,
    text_pages: list[str],
    images: list[PdfImage],
    public_paths: dict[Path, str],
) -> str:
    output = [
        "---",
        "layout: post",
        f"title: {yaml_string(title)}",
        f"date: {date}",
        f"categories: {categories}",
        "---",
        "",
    ]

    images_by_page: dict[int, list[PdfImage]] = {}
    for image in images:
        images_by_page.setdefault(image.page, []).append(image)

    for page_number, page_text in enumerate(text_pages, start=1):
        if not page_text.strip() and page_number not in images_by_page:
            continue
        output.extend(convert_text_page(page_text, page_number, title))
        output.extend(image_markdown(images_by_page.get(page_number, []), public_paths, title))

    return "\n".join(output).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a PDF to a deterministic Jekyll Markdown post."
    )
    parser.add_argument("pdf", type=Path, help="Path to the source PDF")
    parser.add_argument("--title", help="Post title. Defaults to a cleaned PDF filename.")
    parser.add_argument("--slug", help="URL/file slug. Defaults to a slugified title.")
    parser.add_argument(
        "--date",
        required=True,
        help='Jekyll date, for example "2026-05-13 15:50:38 -0700". Required for deterministic output.',
    )
    parser.add_argument("--categories", default="notes", help="Front matter categories")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output Markdown path. Defaults to _posts/<slug>.markdown",
    )
    parser.add_argument(
        "--asset-root",
        type=Path,
        default=Path("assets/images"),
        help="Directory where extracted images are written",
    )
    parser.add_argument(
        "--public-asset-root",
        default="/assets/images",
        help="Public URL root for extracted images",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Markdown and image files",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pdf = args.pdf.expanduser().resolve()
    if not pdf.exists():
        raise SystemExit(f"PDF does not exist: {pdf}")

    require_tool("pdftotext")
    require_tool("pdfimages")

    title = args.title or title_from_pdf_stem(pdf)
    slug = args.slug or slugify(title)
    output_path = args.output or Path("_posts") / f"{slug}.markdown"
    asset_dir = args.asset_root / slug

    if output_path.exists() and not args.force:
        raise SystemExit(f"Refusing to overwrite existing post: {output_path}")

    text_pages = extract_text_pages(pdf)
    image_entries = list_image_entries(pdf)

    with tempfile.TemporaryDirectory(prefix="pdf-to-post-") as temp:
        extracted_images = extract_images(pdf, Path(temp), slug)
        images, public_paths = copy_images(
            extracted_images=extracted_images,
            image_entries=image_entries,
            asset_dir=asset_dir,
            public_asset_dir=args.public_asset_root,
            slug=slug,
            force=args.force,
        )

    markdown = build_markdown(
        title=title,
        date=args.date,
        categories=args.categories,
        text_pages=text_pages,
        images=images,
        public_paths=public_paths,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Wrote {len(images)} image(s) to {asset_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
