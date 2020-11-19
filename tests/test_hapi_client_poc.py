#!/usr/bin/env python

"""Tests for `hapi_client_poc` package."""

import unittest
from ddt import ddt, data, unpack

from hapi_client_poc import get_catalog, get_from_endpoint


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


class TestHAPICatalog(unittest.TestCase):
    def test_a_valid_server_should_provide_a_catalog(self):
        catalog = get_catalog("http://hapi.ftecs.com/hapi/")
        self.assertIsNotNone(catalog)
        self.assertGreater(len(catalog), 0)
        self.assertNotEqual(catalog[0].id, "")
        self.assertIsNotNone(catalog[0].title)

    def test_a_wrong_server_should_return_none(self):
        self.assertIsNone(get_catalog("http://sciqlop.lpp.polytechnique.fr/"), 0)
