from log_analyzer_cli.utils import normalize_error_pattern


def test_normalize_hex_values_as_single_placeholders():
    assert normalize_error_pattern("status 0x404") == "status <HEX>"
