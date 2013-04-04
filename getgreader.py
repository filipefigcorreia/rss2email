# -*- coding: utf-8 -*-
import re
import urllib
import requests
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

def import_history(emailaddress, username, password):
    auth = ClientAuthMethod(username, password)
    reader = GoogleReader(auth)
    userinfo = reader.getUserInfo()
    userId = userinfo['userId']

    if VERBOSE: print "Importing history from Google Reader (account: {0}, userId: {1}, signup@:{2})".format(
        userinfo['userEmail'],
        userinfo['userId'],
        reader.getUserSignupDate())

    reader.buildSubscriptionList()
    cats = [cat.label for cat in reader.getCategories()]
    if VERBOSE: print "Found {0} categories.".format(len(cats))

    cat_url_template = "http://www.google.com/reader/atom/user/{0}/label/{1}"
    cat_url_params = {'n': 250}
    feeds = []

    for cat in cats:
        continuation_code = None
        url = cat_url_template.format(userId, cat)
        if VERBOSE: print "Importing category '{0}' (url: {1})".format(cat, url)
        while True:
            if VERBOSE: print ".",
            if continuation_code:
                full_params = dict(cat_url_params, **{'c':continuation_code})
            else: full_params = cat_url_params

            full_url = url + "?" + urllib.urlencode(full_params)
            data, continuation_code = get_feed_data(full_url, auth)
            cache_feed(RetrievedFeed(data, full_url, None, cat))
            if not continuation_code:
                print ""
                break
    process_feeds([emailaddress] + feeds)


    if VERBOSE: print ""