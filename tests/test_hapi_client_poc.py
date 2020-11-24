#!/usr/bin/env python

"""Tests for `hapi_client_poc` package."""

import unittest
from ddt import ddt, data, unpack
from time import perf_counter
from functools import partial
from dateutil import parser
from datetime import timedelta

from hapi_client_poc import get_catalog, get_info, get_capabilities, get_from_endpoint, build_url, Endpoints, \
    clear_requests_caches, get_data, hapi_server
from hapi_client_poc import parsers as hapi_parers


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
    def setUp(self) -> None:
        self.hapi_server_url = 'http://hapi-server.org/servers/TestData2.0/hapi'

    def test_a_valid_server_should_provide_a_catalog(self):
        catalog = get_catalog(self.hapi_server_url)
        self.assertIsNotNone(catalog)
        self.assertGreater(len(catalog), 0)
        self.assertNotEqual(catalog[0].id, "")
        self.assertIsNotNone(catalog[0].title)

    def test_wrong_status_code_should_discard_data(self):
        self.assertIsNone(hapi_parers.json_response(b'{"status": {"code": 1400, "message": "OK"}}'))
        self.assertIsNone(hapi_parers.json_response(b'{"status": {"code": 1200, "message": "NOK"}}'))

    def test_correct_status_code_should_return_data(self):
        self.assertDictEqual(
            hapi_parers.json_response(b'{"HAPI": "", "status": {"code": 1200, "message": "OK"}, "data": 2}'),
            {'data': 2})

    def test_a_wrong_server_should_return_none(self):
        self.assertIsNone(get_catalog("http://sciqlop.lpp.polytechnique.fr/"), 0)
        self.assertIsNone(get_info("http://sciqlop.lpp.polytechnique.fr/", "some_param"), 0)

    def test_a_valid_server_should_expose_capabilities(self):
        capabilities = get_capabilities(self.hapi_server_url)
        self.assertIsNotNone(capabilities)
        self.assertGreater(len(capabilities.outputFormats), 0)
        self.assertIn(str(capabilities.outputFormats[0]), str(capabilities))

    def test_can_use_all_requests_with_ctx_manager(self):
        with hapi_server(self.hapi_server_url) as server:
            capabilities = server.get_capabilities()
            self.assertIsNotNone(capabilities)
            catalog = server.get_catalog()
            self.assertIsNotNone(catalog)
            info = server.get_info(catalog[0].id)
            self.assertIsNotNone(info)
            self.assertIsNotNone(catalog[0].description)

    def test_when_in_cache_a_request_is_much_faster(self):
        def timeit(f, arg) -> float:
            start = perf_counter()
            f(arg)
            stop = perf_counter()
            return stop - start

        def get_capabilities_no_cache(url):
            clear_requests_caches()
            get_capabilities(url)

        without_cache = sum(map(partial(timeit, get_capabilities_no_cache), [self.hapi_server_url] * 10))
        with_cache = sum(map(partial(timeit, get_capabilities), [self.hapi_server_url] * 1000))
        self.assertGreater(without_cache, with_cache)

    def test_a_valid_dataset_has_description(self):
        dataset = get_catalog(self.hapi_server_url)[0]
        self.assertIn(dataset.id, str(dataset))
        desc = dataset.description
        desc = dataset.description  # increases branch coverage if it works
        self.assertTrue(hasattr(desc, 'startDate'))
        self.assertTrue(hasattr(desc, 'stopDate'))
        self.assertTrue(hasattr(desc, 'parameters'))
        self.assertIn(desc.startDate, str(desc))
        param = list(desc.parameters.values())[0]
        self.assertTrue(hasattr(param, 'name'))
        self.assertTrue(hasattr(param, 'type'))
        self.assertTrue(hasattr(param, 'units'))
        self.assertIn(param.units, str(param))

    def test_a_valid_server_provides_data_for_valid_parameter(self):
        with hapi_server(self.hapi_server_url) as server:
            dataset = server.get_catalog()[0]
            t_start = parser.parse(dataset.description.startDate, fuzzy=True)
            t_stop = parser.parse(dataset.description.stopDate, fuzzy=True)
            t_mid = t_start + ((t_stop - t_start) / 2)
            values = server.get_data(dataset.id, t_mid, t_mid + timedelta(minutes=10))
            self.assertIsNotNone(values)
