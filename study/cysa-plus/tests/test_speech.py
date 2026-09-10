"""The Markdown-to-spoken-prose transform."""

import build_audio as speech


def test_event_ids_are_read_digit_by_digit():
    # "four thousand six hundred and twenty-four" is not what an analyst says.
    assert "4 6 2 4" in speech.speechify("Event 4624 is a logon.")


def test_years_are_left_alone():
    assert "2024" in speech.speechify("Published in 2024.")


def test_numeric_ranges_become_words():
    assert "0 to 7" in speech.speechify("severity 0-7")


def test_silent_operators_are_spoken():
    said = speech.speechify("A = B + C")
    assert "equals" in said and "plus" in said


def test_slash_between_words_becomes_or():
    assert "Unix or network" in speech.speechify("Unix/network events")


def test_markdown_syntax_is_stripped():
    said = speech.speechify("**bold** and `code` and [text](url)")
    assert "*" not in said and "`" not in said and "](" not in said


def test_sentences_end_with_punctuation():
    # Without it the engine runs consecutive lines together.
    assert speech.speechify("No terminator here").endswith(".")


def test_narration_drops_code_blocks():
    said = speech.narrate("# T\n\nBefore.\n\n```bash\nrm -rf /\n```\n\nAfter.\n", "T")
    assert "rm -rf" not in said
    assert "Before." in said and "After." in said


def test_two_column_tables_read_as_key_and_value():
    said = speech.narrate("# T\n\n| Source | Proves |\n|---|---|\n| DNS | Lookups |\n", "T")
    assert "D N S: Lookups." in said
    assert "|" not in said


def test_wider_tables_name_each_column():
    md = "# T\n\n| Source | Proves | Watch |\n|---|---|---|\n| DNS | Lookups | Storms |\n"
    said = speech.narrate(md, "T")
    assert "Source: D N S" in said
    assert "Proves: Lookups" in said
    assert "Watch: Storms" in said
    assert "|" not in said
