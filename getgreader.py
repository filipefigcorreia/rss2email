# -*- coding: utf-8 -*-
from os import path, makedirs, listdir
import sys
import re
import uuid
import urllib
import requests
import cPickle as pickle
from libgreader import GoogleReader, ClientAuthMethod
from rss2email import Feed, process_feeds
try:
    from config import *
except:
    pass

class RetrievedFeed(Feed):
    def __init__(self, data, url, to, folder=None):
        Feed.__init__(self, url, to, folder)
        self.data = data

def get_feed_data(gr_feed_url, auth):
    """
    Request the feed's xml to google-reader using the proper auth
    cookies/params. Also returns continuation code if it exists.
    """
    headers = {'Authorization':'GoogleLogin auth=%s' % auth.auth_token}
    res = requests.get(gr_feed_url, headers=headers, stream=True)
    re_groups = re.search('<gr:continuation>(.*)</gr:continuation>', res.text, re.IGNORECASE)
    if re_groups:
        return res.text, re_groups.group(1)
    else:
        return res.text, None

class FeedCache(object):
    def __init__(self):
        # TODO: make this path a config option
        self.cache_path = path.join(path.expanduser("~"), ".rss2email/greaderimport_cache/")
        if not path.isdir(self.cache_path):
            makedirs(self.cache_path)

    def _get_cache_filenames(self):
        if not path.isdir(self.cache_path):
            return []
        filenames = [path.join(self.cache_path, name) for name in listdir(self.cache_path)]
        return [filename for filename in filenames if path.isfile(filename)]

    def get_count(self):
        return len(self._get_cache_filenames())

    def get_items(self):
        for filename in self._get_cache_filenames():
            yield pickle.load(open(filename, 'r'))

    def add(self, feed):
        while True: # generate short uuid for filename
            rand_filename = path.join(self.cache_path, str(uuid.uuid4())[0:8])
            if not path.exists(rand_filename): break
        pickle.dump(feed, open(rand_filename, 'w'))

    def reset(self):
        import shutil
        shutil.rmtree(self.cache_path)
        makedirs(self.cache_path)

def import_history(emailaddress, username, password, use_cache=False):
    auth = ClientAuthMethod(username, password)
    reader = GoogleReader(auth)
    userinfo = reader.getUserInfo()
    userId = userinfo['userId']

    if VERBOSE: print "Connected to Google Reader (account: {0}, userId: {1}, signedup@:{2})".format(
        userinfo['userEmail'],
        userinfo['userId'],
        reader.getUserSignupDate())

    reader.buildSubscriptionList()
    cats = [cat.label for cat in reader.getCategories()]
    if VERBOSE: print "Found {0} categories.".format(len(cats))

    cat_url_template = "http://www.google.com/reader/atom/user/{0}/label/{1}"
    cat_url_params = {'n': 250} # TODO: make the batch size a config option

    cache = FeedCache()
    if not use_cache and cache.get_count()>0:
        cache.reset()

    if cache.get_count() == 0:
        if VERBOSE: print "Caching feed items..."
        for cat in cats:
            continuation_code = None
            url = cat_url_template.format(userId, cat)
            if VERBOSE: print "Fetching feed items for category '{0}' (url: {1})".format(cat, url)
            while True:
                if VERBOSE:
                    print ".",
                    sys.stdout.flush()
                if continuation_code:
                    full_params = dict(cat_url_params, **{'c':continuation_code})
                else: full_params = cat_url_params

                full_url = url + "?" + urllib.urlencode(full_params)
                data, continuation_code = get_feed_data(full_url, auth)
                cache.add(RetrievedFeed(data, full_url, None, cat))
                if not continuation_code:
                    if VERBOSE: print ""
                    break

    if VERBOSE: print "Loading {0} feed parts from cache".format(cache.get_count())
    for feed in cache.get_items():
        process_feeds(emailaddress, [feed])
