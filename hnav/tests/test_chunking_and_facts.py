"""Chunk -> fact recovery on real data.  [T4/T5]

The benchmark does not hand H-Nav the raw context. It hands it a chunk produced
by ``chunk_text_into_sentences``, which ends in ``" ".join(sentences)`` — so the
newlines between facts become spaces wherever punkt found a boundary, and the
line-anchored ``FACT_RE`` from the brief matches nothing at all.

Every write-side signal depends on exploding a chunk into facts, so this is
checked against the committed dataset, in both the raw and the joined form.
"""
from __future__ import annotations

import pytest

from hnav.adapters.mab_adapter import FACT_RE, explode_facts
from hnav.stage0.m2_retrieval_calibration import _fallback_chunks, build_chunks


def test_raw_context_explodes_completely(sh_6k):
    facts = explode_facts(sh_6k["context"])
    assert len(facts) == 455, "sh_6k is 455 facts; the dataset changed"
    assert [s for s, _ in facts] == list(range(455)), "serials must be exact"
    assert facts[0][1] == "Thomas Kyd was born in the city of London."


def test_line_anchored_regex_alone_fails_on_a_joined_chunk(sh_6k):
    """The failure mode this fallback exists for — asserted, not assumed."""
    joined = " ".join(sh_6k["context"].split("\n"))
    assert FACT_RE.findall(joined) == []
    assert len(explode_facts(joined)) == 455


def test_joined_and_raw_forms_give_identical_facts(sh_6k):
    raw = explode_facts(sh_6k["context"])
    joined = explode_facts(" ".join(sh_6k["context"].split("\n")))
    assert raw == joined


def test_every_fact_survives_chunking(sh_6k):
    """No fact is lost or duplicated across chunk boundaries."""
    chunks, used_fallback = build_chunks(sh_6k["context"], chunk_size=4096)
    assert chunks, "chunker produced nothing"

    recovered = [f for c in chunks for f in explode_facts(c)]
    expected = explode_facts(sh_6k["context"])
    assert [s for s, _ in recovered] == [s for s, _ in expected]
    if not used_fallback:
        assert recovered == expected


def test_fallback_chunker_respects_its_budget():
    text = "\n".join(f"{i}. fact number {i} says something." for i in range(500))
    chunks = _fallback_chunks(text, chunk_size=64)     # 64 tokens ~ 256 chars
    assert len(chunks) > 1
    assert all(len(c) <= 256 + 80 for c in chunks)
    assert len([f for c in chunks for f in explode_facts(c)]) == 500


def test_unparseable_lines_are_skipped_not_guessed(sh_6k):
    """The preamble line is not a fact and must not become one."""
    facts = explode_facts(sh_6k["context"])
    assert not any("Here is a list of facts" in t for _, t in facts)


@pytest.mark.parametrize("blob,expected", [
    ("0. a fact.\n1. another fact.", [(0, "a fact."), (1, "another fact.")]),
    ("intro: 0. a fact. 1. another fact.", [(0, "a fact."), (1, "another fact.")]),
    ("", []),
    ("no facts here at all", []),
    ("7. only one.", [(7, "only one.")]),
])
def test_explode_facts_edge_cases(blob, expected):
    assert explode_facts(blob) == expected
