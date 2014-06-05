import os
import unittest

import mock
from nose_parameterized import parameterized


class TestInclude(unittest.TestCase):

    def tearDown(self):
        if 'CACHING_ENABLED' in os.environ:
            del os.environ['CACHING_ENABLED']

    def test_include(self):
        from pyramid_caching import includeme

        config = mock.Mock(name='config')
        config.registry.settings = {'caching.enabled': True}

        with mock.patch('pyramid_caching.parse_settings') as m_parse:
            includeme(config)

        m_parse.assert_called_once_with(config)
        config.include.assert_has_calls([
            mock.call('.versioner'),
            mock.call('.key_versioner'),
            mock.call('.serializers'),
            mock.call('.cache'),
            ])

    @parameterized.expand([
        ('default', {}, {}, True),
        ('env_true', {'CACHING_ENABLED': 'true'}, {}, True),
        ('env_false', {'CACHING_ENABLED': 'false'}, {}, False),
        ('settings_true', {}, {'caching.enabled': 'true'}, True),
        ('settings_false', {}, {'caching.enabled': 'false'}, False),
        ('both', {'CACHING_ENABLED': 'true'}, {'caching.enabled': 'false'},
         True),
        ('both2', {'CACHING_ENABLED': 'false'}, {'caching.enabled': 'true'},
         False),
        ])
    def test_parse_settings(self, name, envs, settings, expected):
        from pyramid_caching import parse_settings

        config = mock.Mock(name='config')
        config.registry.settings = settings

        os.environ.update(envs)

        parse_settings(config)

        self.assertEqual(config.registry.settings['caching.enabled'], expected)
