import pytest

from app.services.decoders.aprs_position import parse_aprs_position


def test_parses_canonical_position_without_timestamp():
    # The worked example from APRS101.pdf chapter 8.
    position = parse_aprs_position(b"!4903.50N/07201.75W-Test 001234")
    assert position is not None
    assert position.latitude == pytest.approx(49.05833, abs=1e-4)
    assert position.longitude == pytest.approx(-72.02917, abs=1e-4)
    assert position.symbol_table == "/"
    assert position.symbol_code == "-"
    assert position.comment == "Test 001234"


def test_parses_position_with_timestamp():
    position = parse_aprs_position(b"/092345z4903.50N/07201.75W>Moving east")
    assert position is not None
    assert position.symbol_code == ">"
    assert position.comment == "Moving east"


def test_southern_and_eastern_hemispheres_are_negative_and_positive():
    position = parse_aprs_position(b"!3350.00S/15113.00E-Sydney")
    assert position is not None
    assert position.latitude < 0
    assert position.longitude > 0


def test_non_position_info_returns_none():
    assert parse_aprs_position(b">Just a status message, not a position") is None


def test_malformed_position_returns_none():
    assert parse_aprs_position(b"!not a real position at all") is None


def test_empty_info_returns_none():
    assert parse_aprs_position(b"") is None


def _encode_base91(value: int) -> str:
    chars = []
    for _ in range(4):
        chars.append(chr(33 + value % 91))
        value //= 91
    return "".join(reversed(chars))


def _build_compressed_info(latitude: float, longitude: float, symbol_code: str = ">") -> bytes:
    lat_value = round((90 - latitude) * 380926)
    lon_value = round((longitude + 180) * 190463)
    info = f"!/{_encode_base91(lat_value)}{_encode_base91(lon_value)}{symbol_code}!"
    return info.encode("ascii")


def test_compressed_position_round_trips():
    info = _build_compressed_info(49.05833, -72.02917, symbol_code=">")
    position = parse_aprs_position(info)
    assert position is not None
    assert position.latitude == pytest.approx(49.05833, abs=1e-3)
    assert position.longitude == pytest.approx(-72.02917, abs=1e-3)
    assert position.symbol_table == "/"
    assert position.symbol_code == ">"


def test_compressed_position_southern_hemisphere():
    info = _build_compressed_info(-33.85, 151.21)
    position = parse_aprs_position(info)
    assert position is not None
    assert position.latitude == pytest.approx(-33.85, abs=1e-3)
    assert position.longitude == pytest.approx(151.21, abs=1e-3)


def test_compressed_position_with_timestamp():
    body = _build_compressed_info(49.05833, -72.02917).decode("ascii")[1:]  # drop leading '!'
    info = ("/092345z" + body).encode("ascii")
    position = parse_aprs_position(info)
    assert position is not None
    assert position.latitude == pytest.approx(49.05833, abs=1e-3)
