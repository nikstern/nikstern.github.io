# PDF-to-Post Workflow

Use `scripts/pdf_to_markdown_post.py` to convert a PDF into a Jekyll post with extracted image assets. The workflow is deterministic: the script requires an explicit date, uses stable slug-based filenames, ignores soft-mask image artifacts, places images at the end of the PDF page they came from, and does not call an LLM.

## Requirements

- `pdftotext` and `pdfimages` from Poppler must be installed and on `PATH`.
- Run the script from the repository root.

## Command

```sh
scripts/pdf_to_markdown_post.py "/path/to/source.pdf" \
  --title "Post Title" \
  --slug "post-title" \
  --date "2026-05-13 15:50:38 -0700"
```

By default, this writes:

- Markdown post: `_posts/<slug>.markdown`
- Image assets: `assets/images/<slug>/<slug>-000.png`, `assets/images/<slug>/<slug>-001.png`, etc.

Use `--force` only when intentionally regenerating the same post and image assets.

## Agent Checklist

1. Run the script with explicit `--title`, `--slug`, and `--date`.
2. Review the generated Markdown for PDF extraction artifacts, broken line wrapping, or headings that need adjustment.
3. Move images closer to their captions when the page-end placement is not the best reading order.
4. Edit alt text from generic image labels to descriptive labels when the image meaning is clear.
5. Run the site build when the local Ruby environment is available:

```sh
bundle exec jekyll build
```

The script handles deterministic extraction and wiring. Editorial cleanup remains a review step because PDF text order, heading detection, exact image placement, and image captions vary by source document.
