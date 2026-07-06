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
