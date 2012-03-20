import jinja2
import json
import os
import urllib
import urllib2
import webapp2
from google.appengine.ext import db
from google.appengine.api import users
import private

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Profile(db.Model):
    """ A profile corresponds to a GAE user and stores associated metadata for 
        that user.  The key is user.user_id(). """
    access_token = db.StringProperty()

class ConnectPage(webapp2.RequestHandler):
    """ A demo of using OAuth to connect a user's Consumer Notebook account. """
    def get(self):
        user = users.get_current_user()
        if user:
            connect_link = '{0}/oauth2/authorize?client_id={1}&response_type=code&redirect_uri={2}'.format(
                private.CN_HOST,
                private.CLIENT_ID,
                private.REDIRECT_URI
            )
            profile = Profile.get_or_insert(user.user_id())
            template_values = {
                'nickname': user.nickname(), 
                'connect_link': connect_link
            }
            template = jinja_environment.get_template('connect.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

def get_json_response(url, params, method='POST'):
    try:
        if method == 'POST':
            f = urllib2.urlopen(url, urllib.urlencode(params))
        else:
            f = urllib2.urlopen(url + '?' + urllib.urlencode(params))
    except urllib2.HTTPError:
        f = None
    if f:
        response = f.read()
        if response:
            return json.loads(response)
    return None

def get_access_token(user, code=None):
    # First, try the user's existing profile
    profile = Profile.get_or_insert(user.user_id())
    if profile.access_token:
        return profile.access_token

    # If there's no working access token, and if we have a code,
    # then retrieve a new access token
    if code:
        url = '{0}/oauth2/access_token/'.format(private.CN_HOST)
        params = {
            'client_id': private.CLIENT_ID,
            'client_secret': private.CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'redirect_uri': private.REDIRECT_URI, 
            'code': code
        }

        access_token_json = get_json_response(url, params)
        if access_token_json:
            access_token = access_token_json[u'access_token']
            # Save it to the user's profile
            profile.access_token = access_token
            profile.save()
            return access_token
    return None

class BrowsePage(webapp2.RequestHandler):
    """ Continuation of the OAuth demo. """
    def get(self):
        user = users.get_current_user()
        if user:
            # Get the access token
            code = self.request.get('code')
            access_token = get_access_token(user, code)

            # Use the Users API to get the user's username
            cn_username = ''
            profile_url = '{0}/api/v1/my-profile/'.format(private.CN_HOST)
            profile_json = get_json_response(profile_url, {'access_token': access_token}, method='GET')
            if profile_json:
                cn_username = profile_json[u'username']

            # Use the Lists API to get your lists
            lists_url = '{0}/api/v1/my-lists/'.format(private.CN_HOST)
            lists = []
            lists_json = get_json_response(lists_url, {'access_token': access_token}, method='GET')
            if lists_json:
                lists = lists_json[u'objects']

            # Use the Grids API to get your grids
            grids_url = '{0}/api/v1/my-grids/'.format(private.CN_HOST)
            grids = []
            grids_json = get_json_response(grids_url, {'access_token': access_token}, method='GET')
            if grids_json:
                grids = grids_json[u'objects']

            template_values = {
                'nickname': user.nickname(),
                'products': [],
                'lists': lists,
                'grids': grids
            }
            template = jinja_environment.get_template('browse.html')
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp2.WSGIApplication([
        ('/', ConnectPage),
        ('/browse', BrowsePage)],
        debug=True)
