#!/usr/bin/env python

"""Tests for `hapi_client_poc` package."""

import unittest
from ddt import ddt, data, unpack

from hapi_client_poc import get_catalog, get_info, get_from_endpoint, build_url, Endpoints


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

    def test_a_wrong_server_should_return_none(self):
        self.assertIsNone(get_catalog("http://sciqlop.lpp.polytechnique.fr/"), 0)
        self.assertIsNone(get_info("http://sciqlop.lpp.polytechnique.fr/", "some_param"), 0)

    def test_a_valid_dataset_has_description(self):
        dataset = get_catalog("http://hapi.ftecs.com/hapi/")[0]
        self.assertIn(dataset.id, str(dataset))
        desc = dataset.description
        self.assertTrue(hasattr(desc, 'startDate'))
        self.assertTrue(hasattr(desc, 'stopDate'))
        self.assertTrue(hasattr(desc, 'parameters'))
        param = desc.parameters[0]
        self.assertTrue(hasattr(param, 'name'))
        self.assertTrue(hasattr(param, 'type'))
        self.assertTrue(hasattr(param, 'units'))
