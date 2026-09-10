"""Markdown rendering, including regressions for bugs that shipped once."""

import build_offline_html as page


def test_emphasis_around_a_link_containing_code():
    """Bold wrapping a link whose label is a code span.

    This rendered as literal asterisks: the renderer split the text on code
    spans before matching emphasis, so the opening and closing ** landed in
    different segments and never paired.
    """
    out = page.inline("Open **[`file.html`](file.html)** now.")
    assert "**" not in out
    assert "<strong>" in out
    assert "<code>file.html</code>" in out
    # Only .md targets are rewritten to in-page anchors; others stay as-is.
    assert 'href="file.html"' in out


def test_link_label_containing_code():
    out = page.inline("See [`SETUP.md`](SETUP.md) first.")
    assert "](" not in out
    assert '<a href="#setup"><code>SETUP.md</code></a>' in out


def test_code_span_content_is_literal():
    out = page.inline("Run `a **b** c` please.")
    assert "<strong>" not in out
    assert "**b**" in out


def test_html_in_source_is_escaped():
    assert "&lt;script&gt;" in page.inline("<script>alert(1)</script>")


def test_table_becomes_a_scroll_container():
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n"
    out = page.render(md)
    assert '<div class="tw">' in out
    assert "<th>A</th>" in out and "<td>2</td>" in out


def test_blockquote_keeps_block_structure():
    """Quoted headings and paragraphs were flattened into one inline run."""
    out = page.render("> ## Goal\n>\n> Do the thing.\n")
    assert "<blockquote>" in out
    assert "<h2" in out
    assert "## Goal" not in out


def test_fenced_code_is_not_treated_as_markdown():
    out = page.render("```bash\nls -la *.md\n```\n")
    assert "<pre>" in out
    assert "<em>" not in out


def test_headings_get_stable_anchors():
    assert 'id="security-operations"' in page.render("## Security Operations\n")


def test_every_domain_has_an_exam_weight():
    assert sum(page.WEIGHTS.values()) == 100
