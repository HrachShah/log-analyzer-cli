from log_analyzer_cli.utils import normalize_error_pattern, parse_timestamp


def test_parse_timestamp_accepts_space_before_timezone_offset():
    assert parse_timestamp("2025-03-20 10:00:01+01:00").isoformat() == "2025-03-20T10:00:01+01:00"




def test_normalize_hex_values_as_single_placeholders():
    assert normalize_error_pattern("status 0x404") == "status <HEX>"
