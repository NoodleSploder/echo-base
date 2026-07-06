from app.services.decoders.same_codes import describe_event, describe_location


def test_describe_event_known_code():
    assert describe_event("TOR") == "Tornado Warning"


def test_describe_event_unknown_code_falls_back_to_raw():
    assert describe_event("ZZZ") == "ZZZ"


def test_describe_location_entire_county():
    assert describe_location("006037") == "County 037, California"


def test_describe_location_with_subdivision():
    assert describe_location("106037") == "Northwest County 037, California"


def test_describe_location_unknown_state_fips():
    assert describe_location("099999") == "County 999, FIPS state 99"


def test_describe_location_malformed_returns_raw():
    assert describe_location("abc") == "abc"
