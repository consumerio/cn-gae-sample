import jinja2
import json
import os
import urllib2
import webapp2

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class MainPage(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'username': 'audreyr',
        }
        template = jinja_environment.get_template('index.html')
        self.response.out.write(template.render(template_values))

class GridsList(webapp2.RequestHandler):
    def post(self):
        username = self.request.get('username')
        api_key = self.request.get('apikey')
        url = 'https://consumernotebook.com/api/v1/grids/?username={0}&apikey={1}'.format(username, api_key)
        f = urllib2.urlopen(url)
        grids = []
        grids_response = f.read()
        if grids_response:
            grids_json = json.loads(grids_response)
            grids = grids_json[u'objects']

        template_values = {
            'username': username,
            'grids': grids
        }
        template = jinja_environment.get_template('grids-list.html')
        self.response.out.write(template.render(template_values))

app = webapp2.WSGIApplication([
        ('/', MainPage),
        ('/grids-list', GridsList)],
        debug=True)
