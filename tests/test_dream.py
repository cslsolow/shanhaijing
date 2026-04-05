import json
import tempfile
from pathlib import Path
from unittest.mock import patch


def _make_kb(tmp):
    kb = Path(tmp)
    (kb / "wiki/concepts").mkdir(parents=True)
    (kb / "wiki/summaries").mkdir(parents=True)
    (kb / "wiki/summaries/s1.md").write_text("links: [[concept-a]] [[concept-b]]")
    (kb / "wiki/summaries/s2.md").write_text("links: [[concept-c]]")
    (kb / "wiki/concepts/concept-a.md").write_text("---\ntitle: A\ningested: 2020-01-01\n---")
    (kb / "wiki/concepts/concept-b.md").write_text("---\ntitle: B\ningested: 2021-01-01\n---")
    (kb / "wiki/concepts/concept-c.md").write_text("---\ntitle: C\ningested: 2022-01-01\n---")
    return kb


def test_dream_config_defaults():
    with tempfile.TemporaryDirectory() as d:
        from shanhaijing import config
        cfg = config.load(d)
        assert cfg["dream_schedule"] == "0 23 * * *"
        assert cfg["dream_interval_min"] == 45
        assert cfg["dream_token_budget"] == 30000
        assert cfg["dream_concepts_count"] == 7


def test_friction_scores():
    with tempfile.TemporaryDirectory() as tmp:
        from shanhaijing.dream import compute_friction
        kb = _make_kb(tmp)
        scores = compute_friction(kb)
        assert scores[("concept-a", "concept-c")] == 0
        assert scores[("concept-a", "concept-b")] >= 1


def test_generate_round_writes_file():
    with tempfile.TemporaryDirectory() as tmp:
        kb = _make_kb(Path(tmp))
        (kb / "dream").mkdir()

        with patch("shanhaijing.dream.llm.call", return_value="# 梦境\n\n测试内容"):
            from shanhaijing.dream import generate_round
            out_path = generate_round(
                kb_path=kb,
                cfg={"provider": "anthropic", "model": "test"},
                date_str="2026-04-06",
                round_num=1,
                concept="concept-a",
                angle=("contrarian", "反驳最确信的结论"),
                seed="abcd",
                prev_text=None,
                concepts_so_far=[],
                forgotten=[],
                token_budget=30000,
            )
            assert out_path.exists()
            content = out_path.read_text()
            assert "round: 1" in content
            assert "concept-a" in content


def test_run_dream_creates_final(tmp_path):
    kb = _make_kb(tmp_path)
    cfg = {"provider": "anthropic", "model": "test",
           "dream_interval_min": 0, "dream_token_budget": 30000,
           "dream_concepts_count": 3}

    with patch("shanhaijing.dream.llm.call", return_value="# Dream\n\n内容"):
        from shanhaijing.dream import run
        result = run(kb, cfg, dry_run=True)
        assert result["rounds"] >= 1
        final = tmp_path / "dream" / result["date"] / "final.md"
        assert final.exists()
        assert "## 演化记录" in final.read_text()


def test_schedule_adds_crontab(tmp_path):
    with patch("shanhaijing.dream.subprocess.run") as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0
        from shanhaijing.dream import schedule
        schedule(str(tmp_path), "0 23 * * *")
        assert mock_run.called


def test_unschedule_removes_crontab(tmp_path):
    existing = f"0 23 * * * uv run main.py dream {tmp_path}\n"
    with patch("shanhaijing.dream.subprocess.run") as mock_run:
        mock_run.return_value.stdout = existing
        mock_run.return_value.returncode = 0
        from shanhaijing.dream import unschedule
        unschedule(str(tmp_path))
        assert mock_run.called
