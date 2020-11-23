#!/usr/bin/env python

"""Tests for `hapi_client_poc` package."""

import unittest
from ddt import ddt, data, unpack
from time import perf_counter
from functools import partial

from hapi_client_poc import get_catalog, get_info, get_capabilities, get_from_endpoint, build_url, Endpoints, \
    parse_status, clear_requests_caches


@ddt
class TestHAPIUrlsMethods(unittest.TestCase):
    @data(
        ('this_is_a_wrong/server', 'endpoint'),
        ('', 'endpoint'),
        ('unknown_scheme://some.possible.server/hapi', 'endpoint')
    )
    @unpack
    def test_get_should_raises_with_broken_url(self, prefix, endpoint):
        with self.assertRaises(ValueError):
            get_from_endpoint(prefix, endpoint)

    def test_get_from_non_hapi_server_returns_none(self):
        self.assertIsNone(get_from_endpoint("http://sciqlop.lpp.polytechnique.fr/", Endpoints.CAPABILITIES))

    def test_merge_url_without_slashes(self):
        self.assertEqual(build_url('http://server.domain', 'path'), 'http://server.domain/path')

    def test_merge_url_path_without_slashes(self):
        self.assertEqual(build_url('http://server.domain/folder', 'path'), 'http://server.domain/folder/path')

    def test_merge_url_with_leading_slash(self):
        self.assertEqual(build_url('http://server.domain', '/path'), 'http://server.domain/path')

    def test_merge_url_with_trailing_slash(self):
        self.assertEqual(build_url('http://server.domain/', 'path'), 'http://server.domain/path')

    def test_merge_url_with_both_leading_and_trailing_slashes(self):
        self.assertEqual(build_url('http://server.domain/', 'path'), 'http://server.domain/path')


class TestHAPIRequests(unittest.TestCase):
    def test_a_valid_server_should_provide_a_catalog(self):
        catalog = get_catalog("http://hapi.ftecs.com/hapi/")
        self.assertIsNotNone(catalog)
        self.assertGreater(len(catalog), 0)
        self.assertNotEqual(catalog[0].id, "")
        self.assertIsNotNone(catalog[0].title)

    def test_wrong_status_code_should_discard_data(self):
        self.assertIsNone(parse_status({'status': {'code': 1400, 'message': "OK"}}))
        self.assertIsNone(parse_status({'status': {'code': 1200, 'message': "NOK"}}))

    def test_correct_status_code_should_return_data(self):
        self.assertDictEqual(
            parse_status({'HAPI': "", 'status': {'code': 1200, 'message': "OK"}, 'data': 2}), {'data': 2})

    def test_a_wrong_server_should_return_none(self):
        self.assertIsNone(get_catalog("http://sciqlop.lpp.polytechnique.fr/"), 0)
        self.assertIsNone(get_info("http://sciqlop.lpp.polytechnique.fr/", "some_param"), 0)

    def test_a_valid_server_should_expose_capabilities(self):
        capabilities = get_capabilities("http://hapi.ftecs.com/hapi/")
        self.assertIsNotNone(capabilities)
        self.assertGreater(len(capabilities.outputFormats), 0)
        self.assertIn(str(capabilities.outputFormats), str(capabilities))

    def test_when_in_cache_a_request_is_much_faster(self):
        def timeit(f, arg) -> int:
            start = perf_counter()
            f(arg)
            stop = perf_counter()
            return stop - start

        def get_capabilities_no_cache(url):
            clear_requests_caches()
            get_capabilities(url)

        without_cache = sum(map(partial(timeit, get_capabilities_no_cache), ["http://hapi.ftecs.com/hapi/"] * 10))
        with_cache = sum(map(partial(timeit, get_capabilities), ["http://hapi.ftecs.com/hapi/"] * 1000))
        self.assertGreater(without_cache, with_cache)

    def test_a_valid_dataset_has_description(self):
        dataset = get_catalog("http://hapi.ftecs.com/hapi/")[0]
        self.assertIn(dataset.id, str(dataset))
        desc = dataset.description
        desc = dataset.description  # increases branch coverage if it works
        self.assertTrue(hasattr(desc, 'startDate'))
        self.assertTrue(hasattr(desc, 'stopDate'))
        self.assertTrue(hasattr(desc, 'parameters'))
        self.assertIn(desc.startDate, str(desc))
        param = desc.parameters[0]
        self.assertTrue(hasattr(param, 'name'))
        self.assertTrue(hasattr(param, 'type'))
        self.assertTrue(hasattr(param, 'units'))
        self.assertIn(param.units, str(param))
