# -*- coding: utf-8 -*-
import os
from os import path
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

# TODO: make this an option in the config file
WORK_DIR = path.join(path.expanduser("~"), ".rss2email/greaderimport/")

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
        self._cache_path = path.join(WORK_DIR, "cache/")
        if not path.isdir(self._cache_path):
            os.makedirs(self._cache_path)

    def _get_cache_filenames(self):
        if not path.isdir(self._cache_path):
            return []
        filenames = [path.join(self._cache_path, name) for name in os.listdir(self._cache_path)]
        return [filename for filename in filenames if path.isfile(filename)]

    def get_count(self):
        return len(self._get_cache_filenames())

    def get_items(self):
        for filename in self._get_cache_filenames():
            yield pickle.load(open(filename, 'r'))

    def add(self, feed):
        while True: # generate short uuid for filename
            rand_filename = path.join(self._cache_path, str(uuid.uuid4())[0:8])
            if not path.exists(rand_filename): break
        pickle.dump(feed, open(rand_filename, 'w'))

    def reset(self):
        import shutil
        shutil.rmtree(self._cache_path)
        os.makedirs(self._cache_path)

class ProgressLog(object):
    def __init__(self):
        self._plog_filename = path.join(WORK_DIR, "progress.log")
        dirname = path.dirname(self._plog_filename)
        if not path.isdir(dirname):
            os.makedirs(dirname)

    def _exists(self):
        return os.path.isfile(self._plog_filename)

    def reset(self):
        if self._exists():
            os.remove(self._plog_filename)

    def append(self, url):
        with open(self._plog_filename, "a") as plog:
            plog.write(url)
            plog.write("\n")

    def get_urls(self):
        if not self._exists(): return []
        with open(self._plog_filename, "r") as plog:
            plog_str = plog.read()
        return plog_str.splitlines()

def import_history(emailaddress, username, password, use_cache=False, resume=False):
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

    plog = ProgressLog()
    if cache.get_count() == 0:
        if VERBOSE: print "Caching feed items..."
        plog.reset() # an existing progress log is not reliable after rebuilding the cache
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
        if VERBOSE: print "Cache build."

    if VERBOSE: print "\nLoading {0} feed parts from cache ...".format(cache.get_count())
    imported_urls = plog.get_urls()
    if VERBOSE: print "... of which {0} were already imported and will be ignored.".format(len(imported_urls))
    if VERBOSE: print ""
    mailserver = None
    try:
        for feed in cache.get_items():
            if feed.url in imported_urls:
                if VERBOSE: print "Skipping. Already imported {0}".format(feed.url)
                continue
            def report_progress(feed):
                plog.append(feed.url)
            mailserver = process_feeds(emailaddress, [feed], report_progress)
    finally:
        if mailserver:
            try: mailserver.quit()
            except: mailserver.logout()


