#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
db.app = app

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  area = Venue.query.order_by('state').order_by('city').all()
  data = []
  venues = []
  state = area[0].state
  city = area[0].city
  group = {"city": state, "state": city}
  for x in area:    
    if x.state != state or x.city != city:
      data.append(group)
      venues = []
      state = x.state
      city = x.city
      group = {"city": x.city, "state": x.state}
    num = Show.query.filter(Show.venue_id == x.id, Show.start_time > datetime.utcnow()).count()
    venues.append({"id": x.id, "name": x.name, "num_upcoming_shows": num})
    group["venues"] = venues
  data.append(group)
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # search on artists with partial string search. it is case-insensitive.
  search = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike('%' + search + '%')).all()
  count = Venue.query.filter(Venue.name.ilike('%' + search + '%')).count()
  temp = []
  for x in venues:
    num = Show.query.filter(Show.venue_id == x.id, Show.start_time > datetime.utcnow()).count()
    item = {"id": x.id, "name": x.name, "num_upcoming_shows": num}
    temp.append(item)
  response = {"count": count, "data": temp}
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venue = Venue.query.get(venue_id)
  past_shows_count = Show.query.filter(Show.venue_id==venue_id, Show.start_time < datetime.utcnow()).count()
  next_shows_count = Show.query.filter(Show.venue_id==venue_id, Show.start_time > datetime.utcnow()).count()
  past_show = Show.query.join(Show.artist, Show.venue).filter(Show.venue_id==venue_id, Show.start_time < datetime.utcnow()).all()
  next_show = Show.query.join(Show.artist, Show.venue).filter(Show.venue_id==venue_id, Show.start_time > datetime.utcnow()).all()
  past_shows = []
  next_shows= []
  for y in past_show:
    item = {
      "artist_id": y.artist_id, 
      "artist_name": y.artist.name, 
      "artist_image_link": y.artist.image_link, 
      "start_time": y.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    past_shows.append(item)
  for y in next_show:
    item = {
      "artist_id": y.artist_id, 
      "artist_name": y.artist.name, 
      "artist_image_link": y.artist.image_link, 
      "start_time": y.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    next_shows.append(item)
  place={
    "id": venue.id,
    "name": venue.name,
    "genres": [venue.genres],
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": next_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": next_shows_count
  }
  return render_template('pages/show_venue.html', venue=place)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm(request.form)
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)
  error = False
  try:
    venue = Venue(
      name=form.name.data, 
      genres=form.genres.data, 
      address=form.address.data, 
      city=form.city.data, 
      state=form.state.data,
      phone=form.phone.data, 
      website=form.website_link.data, 
      facebook_link=form.facebook_link.data, 
      seeking_talent=form.seeking_talent.data, 
      seeking_description=form.seeking_description.data, 
      image_link=form.image_link.data
    )
    db.session.add(venue)
    db.session.commit()
  except:
    error=True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error:
    # on unsuccessful db insert, flash an error.
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + form.name.data + ' could not be listed.')
    abort(500)
  else:
    # on successful db insert, flash success
    flash('Venue ' + form.name.data + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  if error:
    abort(500)
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # search on artists with partial string search. Ensure it is case-insensitive.
  search = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike('%' + search + '%')).all()
  count = Artist.query.filter(Artist.name.ilike('%' + search + '%')).count()
  temp = []
  for x in artists:
    num = Show.query.filter(Show.artist_id == x.id, Show.start_time > datetime.utcnow()).count()
    item = {"id": x.id, "name": x.name, "num_upcoming_shows": num}
    temp.append(item)
  response = {"count": count, "data": temp}
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  artist = Artist.query.get(artist_id)
  past_shows_count = Show.query.filter(Show.artist_id==artist_id, Show.start_time < datetime.utcnow()).count()
  next_shows_count = Show.query.filter(Show.artist_id==artist_id, Show.start_time > datetime.utcnow()).count()
  past_show = Show.query.join(Show.artist, Show.venue).filter(Show.artist_id==artist_id, Show.start_time < datetime.utcnow()).all()
  next_show = Show.query.join(Show.artist, Show.venue).filter(Show.artist_id==artist_id, Show.start_time > datetime.utcnow()).all()
  past_shows = []
  next_shows= []
  for y in past_show:
    item = {
      "venue_id": y.venue_id, 
      "venue_name": y.venue.name, 
      "venue_image_link": y.venue.image_link, 
      "start_time": y.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    past_shows.append(item)
  for y in next_show:
    item = {
      "venue_id": y.venue_id, 
      "venue_name": y.venue.name, 
      "venue_image_link": y.venue.image_link, 
      "start_time": y.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    }
    next_shows.append(item)
  musician={
    "id": artist.id,
    "name": artist.name,
    "genres": [artist.genres],
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "facebook_link": artist.facebook_link,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": next_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": next_shows_count
  }
  return render_template('pages/show_artist.html', artist=musician)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  # populate form with fields from artist with ID <artist_id>
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  form.name.data = artist.name
  form.genres.data = artist.genres
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm()
  error = False
  try:
    artist = {
      "name": form.name.data,
      "genres": form.genres.data,
      "city": form.city.data,
      "state": form.state.data,
      "phone": form.phone.data,
      "website": form.website_link.data,
      "facebook_link": form.facebook_link.data,
      "seeking_venue": form.seeking_venue.data,
      "seeking_description": form.seeking_description.data,
      "image_link": form.image_link.data
    }
    db.session.query(Artist).filter(Artist.id==artist_id).update(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
    abort(500)
  else:
    # on successful db update, flash success
    flash('Artist ' + form.name.data + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  # populate form with fields from venue with ID <venue_id>
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  form.name.data = venue.name
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.website_link.data = venue.website
  form.facebook_link.data = venue.facebook_link
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description
  form.image_link.data = venue.image_link
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm()
  error = False
  try:
    venue = {
      "name": form.name.data,
      "genres": form.genres.data,
      "address": form.address.data,
      "city": form.city.data,
      "state": form.state.data,
      "phone": form.phone.data,
      "website": form.website_link.data,
      "facebook_link": form.facebook_link.data,
      "seeking_talent": form.seeking_talent.data,
      "seeking_description": form.seeking_description.data,
      "image_link": form.image_link.data
    }
    db.session.query(Venue).filter(Venue.id==venue_id).update(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be updated.')
    abort(500)
  else:
    # on successful db update, flash success
    flash('Artist ' + form.name.data + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm(request.form)
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm(request.form)
  error = False
  try:
    artist = Artist(
      name=form.name.data, 
      city=form.city.data, 
      state=form.state.data, 
      phone=form.phone.data, 
      genres=form.genres.data, 
      image_link=form.image_link.data, 
      facebook_link=form.facebook_link.data, 
      website=form.website_link.data, 
      seeking_venue=form.seeking_venue.data, 
      seeking_description=form.seeking_description.data
    )
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + form.name.data + ' could not be listed.')
    abort(500)
  else:
    # on successful db insert, flash success
    flash('Artist ' + form.name.data + ' was successfully listed!')
    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  data = []
  keys = ["venue_id", "venue_name", "artist_id", "artist_name", "artist_image_link", "start_time"]
  shows = Show.query.join(Show.artist, Show.venue).all()
  for x in shows:
    values = [
      x.venue_id,
      x.venue.name, 
      x.artist_id, 
      x.artist.name,
      x.artist.image_link,
      x.start_time.strftime("%m/%d/%Y, %H:%M:%S")
    ]
    data.append(dict(zip(keys, values)))
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm(request.form)
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_shows_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  form = ShowForm(request.form)
  try:
    show = Show(artist_id=form.artist_id.data, venue_id=form.venue_id.data, start_time=form.start_time.data)
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info)
  finally:
    db.session.close()
  if error:
    # on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
    abort(500)
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
