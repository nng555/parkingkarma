#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers

import jinja2
import webapp2
import base64
import os
from time import gmtime, strftime

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Karma(ndb.Model):
    license = ndb.StringProperty()
    time = ndb.StringProperty()
    message = ndb.StringProperty()
    location = ndb.StringProperty()
    karmaVal = ndb.BooleanProperty()

class Plate(ndb.Model):
    license = ndb.StringProperty()
    score = ndb.IntegerProperty()

class IndexHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render({'karma_url': blobstore.create_upload_url('/karma')}))

class KarmaHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        karma = Karma()
        setattr(karma, 'time', strftime("%Y-%m-%d %H:%M:%S"))
        setattr(karma, 'karmaVal', (self.request.get('karmaVal') == "on"))
        karma_keys = ['license', 'message', 'location']
        for key in karma_keys:
            val = self.request.get_all(key)
            setattr(karma, key, val[0])
        karma.put()
        plates = Plate.query(Plate.license == karma.license).fetch(1)
        if(plates):
            plate = plates[0]
            if(karma.karmaVal):
                plate.score = plate.score + 1
            else:
                plate.score = plate.score - 1
            plate.put()
        else:
            plate = Plate()
            setattr(plate, 'license', karma.license)
            if(karma.karmaVal):
                setattr(plate, 'score', 1)
            else:
                setattr(plate, 'score', -1)
            plate.put()
        self.redirect("/plate/{}".format(plate.license))

class PlateHandler(webapp2.RequestHandler):
    def get(self, license):
        plates = Plate.query(Plate.license == license).fetch(1)
        if(plates):
            plate = plates[0]
        else:
            self.redirect("/")
        karmas = Karma.query(Karma.license == license and Karma.message != "").fetch()
        template = JINJA_ENVIRONMENT.get_template('templates/plate.html')
        self.response.write(template.render({'karmas': karmas, 'plate': plate}))

# [START app]
app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/karma', KarmaHandler),
    ('/plate/(.+)', PlateHandler)
], debug=True)
# [END app]
