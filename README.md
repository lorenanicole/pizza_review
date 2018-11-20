## Pizza Review Aggregator

### Challenge

- Build a web page that accepts the name of a pizza restaurant in New York
- The response should display the `n` most recent Yelp reviews for this restaurant
- The web page should also display the average score (0-5) of the returned reviews

### Setup

This is a Flask Python 3.6.2 app. 

You'll need to register a Yelp application via [Yelp's Create App](https://www.yelp.com/developers/v3/manage_app) dash. From there you'll received a `client_id` and an `api_key`, which you'll want to put into a yaml file located at `app/config.yml`.

Now you're ready to spin up the app:

*Option 1: Use Docker Compose*
```
cd app
docker-compose up -d  # Runs detached

# To spin down
docker-compose down
```

Note: Since the `docker-compose.yml` uses a mountable volume directory, if you were to make a code change and rebuild [you'd have to specify the following command](https://stackoverflow.com/a/35231363/3011436) before calling `docker-compose up -d`:

```
docker-compose build --no-cache
# Flow as specified above
```

*Option 2: Run from CLI directly(=*
```
cd app
pip3 install -r requirements.txt
python3 app.py 
```

### Finding reviews for a pizza shop in New York

You can either hit the API directly or view the information in the browser.

To hit the API directly:

```
curl -X POST 'http://localhost:5000/restaurant/reviews' -H 'Content-Type: application/json' -d '{"name":"bleecker street", "location":"new+york", "limit":26}' | python -mjson.tool
```

Or else you can enter `http://localhost:5000` in your browser of choice and enter the information requested on the form, hit enter, and viola!
