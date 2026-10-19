import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from rates import RateCache, RateError, Snapshot, fetch_rate
from server import command

class RatesTest(unittest.TestCase):
    def test_shared_cache_and_stale_backoff(self):
        clock = [0]
        snapshot = Snapshot(60, datetime.now(timezone.utc), datetime.now(timezone.utc))
        fetch = Mock(side_effect=[snapshot, RateError(), snapshot])
        cache = RateCache(fetch, lambda: clock[0])
        for _ in range(10): self.assertEqual(cache.get().rate, 60)
        self.assertEqual(fetch.call_count, 1)
        clock[0] = 3600
        self.assertTrue(cache.get().stale)
        cache.get()
        self.assertEqual(fetch.call_count, 2)
        clock[0] += 60
        self.assertFalse(cache.get().stale)

    def test_empty_failure_does_not_retry_every_visitor(self):
        fetch = Mock(side_effect=RateError())
        cache = RateCache(fetch, lambda: 0)
        for _ in range(3):
            with self.assertRaises(RateError): cache.get()
        self.assertEqual(fetch.call_count, 1)

    @patch('rates.requests.get')
    def test_provider_validation(self, get):
        response = get.return_value
        response.json.return_value = {'result':'success','base_code':'USD','conversion_rates':{'DOP':60.5},'time_last_update_unix':1700000000}
        self.assertEqual(fetch_rate().rate, 60.5)
        for value in [-1, float('nan'), True, 'bad']:
            response.json.return_value['conversion_rates']['DOP'] = value
            with self.assertRaises(RateError): fetch_rate()
        response.json.return_value = {'result':'error'}
        with self.assertRaises(RateError): fetch_rate()

    def test_host_and_prefix(self):
        args = command({'IP':'::1','PORT':'8100','BASE_PATH':'/app-dolar/'})
        self.assertIn('--server.address=::1', args)
        self.assertIn('--server.baseUrlPath=app-dolar', args)
        with self.assertRaises(ValueError): command({'BASE_PATH':'../bad'})
        with self.assertRaises(ValueError): command({'PORT':'0'})

if __name__ == '__main__': unittest.main()
