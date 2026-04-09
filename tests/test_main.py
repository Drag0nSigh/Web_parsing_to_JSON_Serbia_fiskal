"""Тесты для src/main.py."""

import importlib
import json
import sys
from unittest.mock import patch

import pytest

_RECEIPT = {
    "fiscalDocumentNumber": "CHK-1",
    "totalSum": "100.00",
    "items": [{"name": "Test", "quantity": 1, "price": 100, "sum": 100}],
    "user": "Shop",
    "dateTime": "2025-01-01T12:00:00",
}

_MOCK_PARSE_RESULT = [
    {
        "ticket": {
            "document": {
                "receipt": _RECEIPT,
            }
        }
    }
]


def _run_main(monkeypatch, tmp_path, argv, parse_side_effect=None, parse_return=None):
    """Патчим parse_serbian_fiscal_url в модуле парсера до import main — иначе тянется Selenium/WDM."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", argv)
    kwargs = {"side_effect": parse_side_effect} if parse_side_effect is not None else {"return_value": parse_return}
    with patch("parser.fiscal_parser.parse_serbian_fiscal_url", **kwargs):
        sys.modules.pop("main", None)
        main_mod = importlib.import_module("main")
        main_mod.main()


class TestMain:
    def test_main_with_url_arg(self, tmp_path, monkeypatch):
        _run_main(
            monkeypatch,
            tmp_path,
            ["main.py", "https://example.com/receipt"],
            parse_return=_MOCK_PARSE_RESULT,
        )

        out = tmp_path / "output.json"
        assert out.exists()
        assert json.loads(out.read_text(encoding="utf-8")) == _MOCK_PARSE_RESULT

    def test_main_default_url(self, tmp_path, monkeypatch):
        _run_main(monkeypatch, tmp_path, ["main.py"], parse_return=_MOCK_PARSE_RESULT)

        assert (tmp_path / "output.json").exists()

    def test_main_parse_error(self, tmp_path, monkeypatch, capsys):
        _run_main(
            monkeypatch,
            tmp_path,
            ["main.py", "https://bad"],
            parse_side_effect=OSError("network"),
        )

        err = capsys.readouterr().err
        assert "network" in err

    def test_main_empty_items(self, tmp_path, monkeypatch):
        receipt = dict(_RECEIPT)
        receipt["items"] = []
        result = [{"ticket": {"document": {"receipt": receipt}}}]
        _run_main(monkeypatch, tmp_path, ["main.py", "https://x"], parse_return=result)

        assert (tmp_path / "output.json").exists()
