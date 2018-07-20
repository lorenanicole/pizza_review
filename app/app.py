import json
import logging
import re
from pathlib import Path
from statistics import mean
from urllib.parse import urlencode

import requests
import yaml
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify, Response, render_template

app = Flask(__name__)

CURRENT_DIR_PATH = Path(__file__).resolve().parent

CONFIG = yaml.load(open('{}/config.yml'.format(CURRENT_DIR_PATH)))

logging.basicConfig(filename='app.log', level=logging.DEBUG)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/restaurant', methods=['GET'])
def get_restaurants():
    """
    Search Yelp to find restaurant in a given location.

    :param restaurant_name: str of the restaurant name looking up
    :param location: str of the city name inquiring after
    :param limit: optional param specifying limit of restaurants to return

    :return json of matching restaurant(s)
    """

    restaurant_name = request.args.get('name')
    location = request.args.get('location')
    limit = int(request.args.get('limit', 1))

    try:
        yelp_api = YelpApi(api_key=CONFIG.get('yelp_api_key'),
                   client_id=CONFIG.get('yelp_client_id'))
        restaurants = yelp_api.search_businesses(restaurant_name, location, limit)
        return jsonify(restaurants)
    except Exception as e:
        logging.error('Exception processing data from Yelp: {}'.format(e))
        return Response({'error': 'Exception processing data from Yelp.'},
                        status=400, mimetype='application/json')


@app.route('/restaurant/reviews', methods=['POST'])
def get_restaurant_reviews():
    """
    Uses Yelp to find the business matching search criteria and scrapes for Yelp reviews of that
    business using Beautiful Soup. Accepts either a JSON post body or a FORM URLENCODED body.

    :param restaurant_name: str of the restaurant name looking up
    :param location: str of the city name inquiring after
    :param limit: optional param specifying limit of restaurants to return

    :return json of restaurant reviews and avg review.
    """

    request_type = request.headers.get('Content-Type')

    if request_type == 'application/x-www-form-urlencoded':
        data = request.form
    elif request_type == 'application/json':
        data = json.loads(request.data)

    logging.info('Received request with params: {}'.format(data))

    restaurant_name = data.get('name')
    location = data.get('location')
    reviews_requested = int(data.get('limit', 1))

    try:
        yelp_api = YelpApi(api_key=CONFIG.get('yelp_api_key'),
                   client_id=CONFIG.get('yelp_client_id'))
        restaurant = yelp_api.search_businesses(restaurant_name, location)[0]
    except Exception as e:
        logging.error('Exception processing data from Yelp: {}'.format(e))
        return Response({'error': 'Exception processing data from Yelp.'},
                        status=400, mimetype='application/json')

    restaurant_categories = list(map(lambda r: r.get('alias'), restaurant['categories']))

    if 'pizza' not in restaurant_categories:
        return Response({'error': 'No pizza restaurants by the name and location found.'},
                        status=404, mimetype='application/json')

    restaurant_reviews_url = restaurant.get('url')
    restaurant_reviews_text, restaurant_review_stars = [], []

    while reviews_requested > 0:
        response = requests.get(restaurant_reviews_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # The 'class' name for where to find the next reviews ordered by time DESC includes 'next'
        restaurant_reviews_url = soup.find_all('a', {'class': 'u-decoration-none next pagination-links_anchor'})
        restaurant_reviews_url = restaurant_reviews_url[0].attrs.get('href')

        review_content = soup.find_all('div', {'class': 'review-content'})
        review_stars = list(map(lambda review: review.find_all('div', {'class': 'i-stars'})[0].attrs.get('title'),
                                review_content))
        review_content = list(map(lambda review: review.text, review_content))

        if reviews_requested < len(review_content):   # want 10, have 20
            restaurant_reviews_text += review_content[0:reviews_requested]
            restaurant_review_stars += review_stars[0:reviews_requested]
            reviews_requested -= reviews_requested
        elif reviews_requested >= len(review_content):
            restaurant_reviews_text += review_content
            restaurant_review_stars += review_stars
            reviews_requested -= len(review_content)

        logging.info('Reviews to collect: {}'.format(reviews_requested))

    restaurant_reviews = []

    for i, val in enumerate(restaurant_reviews_text):  # Zip review text with review rating
        restaurant_reviews.append(dict(
            zip(['text', 'stars'],
                [restaurant_reviews_text[i], float(re.sub("[^0-9.]", "", restaurant_review_stars[i]))])
        ))

    avg_review = mean(map(lambda r: r.get('stars'), restaurant_reviews))

    return jsonify({
        'restaurant': restaurant,
        'reviews': restaurant_reviews,
        'avg_review': avg_review
    })


class YelpApi(object):
    """
    Lightweight wrapper to make requests against Yelp API.
    """

    api_url = u'https://api.yelp.com/v3'

    def __init__(self, api_key, client_id):
        self.api_key = api_key
        self.client_id = client_id

    def search_businesses(self, term, location, limit=1):
        """
        :param term: (str) business search query term e.g. business name, business type
        :param location: (str) name of location to search e.g. New York
        :param limit: (int) optional - limit of businesses to return matching search criteria

        :return json of matching business(es)
        """

        query_params = {
            'term': term,
            'location': location,
            'limit': limit
        }

        query_string = urlencode(query_params)

        business_search_endpoint = u'{}/{}/{}?{}'.format(
            YelpApi.api_url, 'businesses', 'search', query_string
        )

        try:
            response = requests.get(
                business_search_endpoint,
                headers={'Authorization': 'Bearer {}'.format(self.api_key)}
            )
            restaurants = response.json().get('businesses')[0:limit]
            return restaurants
        except Exception as e:
            raise Exception('Exception processing Yelp data')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
