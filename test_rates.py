import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from rates import RateCache, RateError, Snapshot, fetch_rate, cross_rate, convert
from server import command

class RatesTest(unittest.TestCase):
    def test_shared_cache_and_stale_backoff(self):
        clock = [0]
        snapshot = Snapshot({"USD":1,"DOP":60,"EUR":0.8}, datetime.now(timezone.utc), datetime.now(timezone.utc))
        fetch = Mock(side_effect=[snapshot, RateError(), snapshot])
        cache = RateCache(fetch, lambda: clock[0])
        for _ in range(10): self.assertEqual(cache.get().rates["DOP"], 60)
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
        response.json.return_value = {'result':'success','base_code':'USD','rates':{'USD':1,'DOP':61.266775,'EUR':0.890861,'COP':3174.489272},'time_last_update_unix':1700000000}
        self.assertEqual(fetch_rate().rates["DOP"], 61.266775)
        for value in [-1, float('nan'), True, 'bad']:
            response.json.return_value['rates']['DOP'] = value
            with self.assertRaises(RateError): fetch_rate()
        for payload in [[], None, {'result':'success','base_code':'USD','rates':{'EUR':0.8},'time_last_update_unix':1700000000}, {'result':'success','base_code':'USD','rates':{'USD':2},'time_last_update_unix':1700000000}]:
            response.json.return_value = payload
            with self.assertRaises(RateError): fetch_rate()
        response.json.return_value = {'result':'error'}
        with self.assertRaises(RateError): fetch_rate()

    def test_cross_rates_and_invalid_amounts(self):
        snapshot = Snapshot({"USD":1,"DOP":60,"EUR":0.8}, datetime.now(timezone.utc), datetime.now(timezone.utc))
        self.assertEqual(convert(snapshot, 100, "USD", "DOP"), 6000)
        self.assertEqual(convert(snapshot, 80, "EUR", "DOP"), 6000)
        self.assertEqual(convert(snapshot, 6000, "DOP", "EUR"), 80)
        self.assertEqual(convert(snapshot, 7, "EUR", "EUR"), 7)
        self.assertEqual(convert(snapshot, 0, "USD", "DOP"), 0)
        with self.assertRaises(ValueError): cross_rate(snapshot, "XXX", "DOP")
        for amount in [-1, float('nan'), float('inf'), True]:
            with self.assertRaises(ValueError): convert(snapshot, amount, "USD", "DOP")

    def test_host_and_prefix(self):
        args = command({'IP':'::1','PORT':'8100','BASE_PATH':'/app-dolar/'})
        self.assertIn('--server.address=::1', args)
        self.assertIn('--server.baseUrlPath=app-dolar', args)
        with self.assertRaises(ValueError): command({'BASE_PATH':'../bad'})
        with self.assertRaises(ValueError): command({'PORT':'0'})

if __name__ == '__main__': unittest.main()
