from pathlib import Path

import envref


def test_parse_env_file(tmp_path: Path) -> None:
    path = tmp_path / ".env.example"
    path.write_text("FOO=bar\n# comment\nBAR=\nexport BAZ=1\n", encoding="utf-8")
    assert envref.parse_env_file(path) == {"FOO", "BAR", "BAZ"}


def test_scan_directory(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        'import os\nvalue = os.getenv("FOO")\nother = os.environ["BAR"]\n',
        encoding="utf-8",
    )
    (tmp_path / "app.js").write_text(
        'const a = process.env.BAZ;\nconst b = process.env["QUX"];\n',
        encoding="utf-8",
    )
    refs, scanned = envref.scan_directory(tmp_path)
    assert refs == {"FOO", "BAR", "BAZ", "QUX"}
    assert scanned == 2


def test_cli_reports_drift(tmp_path: Path, capsys) -> None:
    (tmp_path / "app.py").write_text('import os\nprint(os.getenv("NEW_VAR"))\n', encoding="utf-8")
    (tmp_path / ".env.example").write_text("OLD_VAR=1\n", encoding="utf-8")
    code = envref.main([str(tmp_path), "--fail-on", "none"])
    captured = capsys.readouterr()
    assert code == 0
    assert "NEW_VAR" in captured.out
    assert "OLD_VAR" in captured.out
