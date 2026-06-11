from satlight.assets import ensure_placeholder_icons

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_generates_missing_icons(tmp_path):
    written = ensure_placeholder_icons(tmp_path)
    names = {p.name for p in written}
    assert names == {"starlink.png", "iss.png", "default.png"}
    for path in written:
        assert path.read_bytes().startswith(_PNG_SIGNATURE)


def test_is_idempotent(tmp_path):
    ensure_placeholder_icons(tmp_path)
    assert ensure_placeholder_icons(tmp_path) == []
