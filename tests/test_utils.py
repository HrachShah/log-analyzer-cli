"""Tests for log_analyzer_cli.utils helpers."""

from __future__ import annotations

import pytest

from log_analyzer_cli.utils import normalize_error_pattern


class TestNormalizeErrorPattern:
    """Tests for normalize_error_pattern."""

    def test_ipv4_address(self):
        assert normalize_error_pattern("user 42 logged in from 192.168.1.1") == \
            "user <NUM> logged in from <IP>"

    def test_ipv4_with_port(self):
        assert normalize_error_pattern("connect to db.local:5432 failed") == \
            "connect to <HOST>:<PORT> failed"

    def test_url_collapsed_to_single_placeholder(self):
        # Previously this became "https:<PATH>" because the host pattern
        # required a single-segment hostname and the path rule then ate
        # the rest of the URL up to end of line.
        assert normalize_error_pattern("GET https://api.example.com/foo?x=1") == \
            "GET <URL>"

    def test_url_with_port_and_path(self):
        assert normalize_error_pattern("call https://example.com:443/v1/items") == \
            "call <URL>"

    def test_url_with_multi_label_subdomain(self):
        assert normalize_error_pattern("request to http://internal.svc.cluster.local:8080/api") == \
            "request to <URL>"

    def test_multi_segment_hostname(self):
        # api.example.com is two segments before the TLD; the old
        # single-segment pattern only matched "host.tld" and let
        # "api.example.com" leak through to the path rule.
        assert normalize_error_pattern("timeout contacting api.example.com") == \
            "timeout contacting <HOST>"

    def test_ipv6_address(self):
        # The old path-first-then-numbers rules turned 2001:db8::1 into
        # "<NUM>:db8::<PORT>". Match it as a single IPv6 placeholder.
        assert normalize_error_pattern("request 99 from 2001:db8::1") == \
            "request <NUM> from <IPV6>"

    def test_uuid_collapsed(self):
        assert normalize_error_pattern(
            "request 5f3a4b2c-1234-5678-9abc-def012345678 done"
        ) == "request <UUID> done"

    def test_path_not_swallowed_by_url_rule(self):
        # A bare relative path is still a path, not a URL.
        assert normalize_error_pattern("Traceback: 0xdeadbeef at /usr/local/bin/app") == \
            "Traceback: <HEX> at <PATH>"

    def test_version_numbers_preserved_when_not_path(self):
        # v2.3.4 with no surrounding TLD should not get mangled beyond
        # replacing the embedded numbers.
        assert normalize_error_pattern("error in v2.3.4 build 1234") == \
            "error in v2.<NUM>.<NUM> build <NUM>"

    def test_email_keeps_localpart(self):
        assert normalize_error_pattern("user alice@service.io logged in") == \
            "user alice@<HOST> logged in"
