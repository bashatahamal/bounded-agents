from bounded.memory import DistilledRule, JsonlMemoryStore, Provenance, distill


def test_add_and_list_roundtrip(tmp_path):
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")

    store.add("reminders", "checks tasks in the evening", Provenance.HUMAN_MANUAL)
    store.add("scoring", "prefers large companies", Provenance.HUMAN_FEEDBACK)

    all_entries = store.list()
    assert len(all_entries) == 2
    contents = {e.content for e in all_entries}
    assert contents == {"checks tasks in the evening", "prefers large companies"}


def test_list_filters_by_scope(tmp_path):
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")
    store.add("reminders", "a", Provenance.HUMAN_MANUAL)
    store.add("scoring", "b", Provenance.HUMAN_MANUAL)

    reminders = store.list(scope="reminders")

    assert len(reminders) == 1
    assert reminders[0].content == "a"


def test_list_ranks_by_provenance_human_manual_first(tmp_path):
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")
    # Added in an order that would be wrong if sorting were by insertion order.
    store.add("reminders", "inferred fact", Provenance.LLM_INFERRED)
    store.add("reminders", "manual fact", Provenance.HUMAN_MANUAL)
    store.add("reminders", "feedback fact", Provenance.HUMAN_FEEDBACK)

    entries = store.list(scope="reminders")

    assert [e.provenance for e in entries] == [
        Provenance.HUMAN_MANUAL,
        Provenance.HUMAN_FEEDBACK,
        Provenance.LLM_INFERRED,
    ]


def test_add_dedups_exact_match_case_and_whitespace_insensitive(tmp_path):
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")
    first = store.add("reminders", "checks tasks in the evening", Provenance.HUMAN_MANUAL)

    duplicate = store.add("reminders", "  Checks Tasks In The Evening  ", Provenance.HUMAN_MANUAL)

    assert duplicate.id == first.id
    assert len(store.list()) == 1


def test_add_does_not_dedup_across_different_scopes(tmp_path):
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")
    store.add("reminders", "same text", Provenance.HUMAN_MANUAL)
    store.add("scoring", "same text", Provenance.HUMAN_MANUAL)

    assert len(store.list()) == 2


def test_store_persists_across_instances(tmp_path):
    path = tmp_path / "memory.jsonl"
    JsonlMemoryStore(path).add("reminders", "durable fact", Provenance.HUMAN_MANUAL)

    reloaded = JsonlMemoryStore(path)

    assert len(reloaded.list()) == 1
    assert reloaded.list()[0].content == "durable fact"


def test_delete_removes_matching_entry(tmp_path):
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")
    keep = store.add("reminders", "keep this", Provenance.HUMAN_MANUAL)
    gone = store.add("reminders", "delete this", Provenance.HUMAN_MANUAL)

    result = store.delete(gone.id)

    assert result is True
    remaining = store.list()
    assert len(remaining) == 1
    assert remaining[0].id == keep.id


def test_delete_returns_false_for_unknown_id(tmp_path):
    store = JsonlMemoryStore(tmp_path / "memory.jsonl")
    store.add("reminders", "keep this", Provenance.HUMAN_MANUAL)

    result = store.delete("not-a-real-id")

    assert result is False
    assert len(store.list()) == 1


def test_delete_persists_across_instances(tmp_path):
    path = tmp_path / "memory.jsonl"
    store = JsonlMemoryStore(path)
    entry = store.add("reminders", "durable fact", Provenance.HUMAN_MANUAL)

    store.delete(entry.id)
    reloaded = JsonlMemoryStore(path)

    assert reloaded.list() == []


class _StubLLM:
    def __init__(self, text: str):
        self.text = text

    def complete(self, *, user_input: str, system_prompt: str | None = None) -> str:
        return self.text


def test_distill_happy_path_extracts_rules():
    llm = _StubLLM(
        '```json\n{"rules": [{"content": "prefers evening reminders", "scope": "reminders"}]}\n```'
    )

    rules = distill(llm=llm, prompt="extract rules")

    assert rules == [DistilledRule(content="prefers evening reminders", scope="reminders")]


def test_distill_returns_empty_list_on_unparseable_output():
    llm = _StubLLM("this is not json at all")

    rules = distill(llm=llm, prompt="extract rules")

    assert rules == []


def test_distill_skips_malformed_rule_entries_but_keeps_valid_ones():
    llm = _StubLLM(
        '{"rules": ['
        '{"content": "valid rule", "scope": "reminders"}, '
        '{"content": "missing scope"}, '
        '"not even a dict"'
        "]}"
    )

    rules = distill(llm=llm, prompt="extract rules")

    assert rules == [DistilledRule(content="valid rule", scope="reminders")]
