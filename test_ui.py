import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from rates import Snapshot, RateError

class DashboardTest(unittest.TestCase):
    def test_conversion_and_provider_failure(self):
        value = Snapshot({"USD":1,"DOP":60,"EUR":0.8}, datetime.now(timezone.utc), datetime.now(timezone.utc))
        with patch('rates.RateCache.get', return_value=value):
            app = AppTest.from_file('app.py').run(timeout=30)
            self.assertEqual(len(app.exception), 0)
            self.assertIn('6,000.00', app.success[0].value)
            app.number_input[0].set_value(2.0).run()
            self.assertIn('120.00', app.success[0].value)
            self.assertEqual(app.selectbox[0].value, 'USD')
            self.assertEqual(app.selectbox[1].value, 'DOP')
            app.selectbox[0].set_value('EUR').run()
            self.assertIn('150.00 DOP', app.success[0].value)
            app.button[1].click().run()
            self.assertEqual(app.selectbox[0].value, 'DOP')
            self.assertEqual(app.selectbox[1].value, 'EUR')
            self.assertIn('0.03 EUR', app.success[0].value)
            app.selectbox[0].set_value('EUR').run()
            self.assertIn('2.00 EUR', app.success[0].value)
            history = app.session_state['readings_multi']
            self.assertLessEqual(len(history), 50)
            self.assertIn('Origen', history[0])
        with patch('rates.RateCache.get', side_effect=RateError('No disponible')):
            app = AppTest.from_file('app.py').run(timeout=30)
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.error[0].value, 'No disponible')
