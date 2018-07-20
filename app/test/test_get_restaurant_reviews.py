import json
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from ..app.app import app

CURRENT_DIR_PATH = Path(__file__).resolve().parent
FIXTURES = '{}/fixtures'.format(CURRENT_DIR_PATH)


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.business_response = json.load(open('{}/{}'.format(FIXTURES, 'yelp_api_business_response.json')))
        self.reviews_response = open('{}/{}'.format(FIXTURES, 'yelp_business_url_response.html')).read()

    @patch('app.app.YelpApi.search_businesses', return_value=Mock())
    @patch('requests.get', return_value=Mock())
    def test_get_restaurant_reviews_happy_path(self, mocked_requests_response, mocked_yelp):
        mocked_yelp.return_value = [self.business_response]
        mocked_requests_response.content.return_value = self.reviews_response

        response = self.app.post('/restaurant/reviews',
                                 data={"name":"bleecker street", "location":"new york", "limit": 10}
                                 )
        self.assertEqual(len(response.get('reviews')), 10)

if __name__ == '__main__':
    unittest.main()