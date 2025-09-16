import noted


def test_ai_summarize_local():
    text = """
    This is a long paragraph about something important.
    It contains multiple lines.
    Summary: this should be included.
    Another detail line.
    Conclusion: final thoughts.
    """
    out = noted.EditableBoxApp._ai_generate_locally(text, action="summarize")
    assert isinstance(out, str) and "Summary:" in out


def test_ai_rewrite_local():
    text = "A   sentence    with    irregular   spacing that should be wrapped to a reasonable width."
    out = noted.EditableBoxApp._ai_generate_locally(text, action="rewrite")
    assert isinstance(out, str) and len(out) > 0 and "  " not in out


def test_ai_proofread_local():
    text = "This is a sentence without punctuation Another one here"
    out = noted.EditableBoxApp._ai_generate_locally(text, action="proofread")
    assert isinstance(out, str) and out.strip().endswith(('.', '!', '?'))
