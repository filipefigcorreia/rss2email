rss2imap
========

An adaptation of rss2email that uses IMAP directly, extended to import historic feed items from google reader.

## What does it look like?

Well, with the shipping CSS in `config.py`, it looks like this:

<img src="https://raw.github.com/rcarmo/rss2email/screenshots/mail.app.1.jpg" style="max-width: 100%; height: auto;">

## What about mobile?

Well, it works fine with the Gmail app on both Android and iOS, as well as the native IMAP clients:

<img src="https://raw.github.com/rcarmo/rss2email/screenshots/gmail.ios.1.jpg" width="25%"> <img src="https://raw.github.com/rcarmo/rss2email/screenshots/mail.ios.1.jpg" width="25%"> <img src="https://raw.github.com/rcarmo/rss2email/screenshots/gmail.android.1.jpg" width="25%"> <img src="https://raw.github.com/rcarmo/rss2email/screenshots/mail.android.1.jpg" width="25%">

As long as you sync, all the text will be available off-line (images are cached at the whim of the MUA).

The Gmail app ignores CSS and may have weird behaviors with long bits of text, though.

## Main Features

* E-mail is injected directly via IMAP (so no delays or hassles with spam filters)
* Feeds can be grouped into IMAP folders -- no inbox clutter!
* Generates E-mail headers for threading, so a post that references another post (or that includes the same link) will show up as a thread on decent MUAs. Also, posts from the same feed will be part of the same thread)
* Can (optionally) include images inline (as `data:` URIs for now -- which only works properly on iOS/Mac -- soon as MIME attachments) or as attachments (which works with most MUAs)
* Can (optionally) remove read (but not flagged) items automatically
* Tries to retrieve broken image links of old feed items from archive.org
* Tries to figure out the folder when importing from an OPML file (only tested with GReader exported OPML files)

## Google Reader import

* Imports all feed items from a supplied google reader account
* Stores feed items retrieved from google reader on a filesystem-based cache that is recreated on each run, except if the --use-cache switch is used.
* Tracks progress of which feed items in the cache were already imported, and is able to resume where it left off when the --use-cache switch is used (useful to recover interrupted imports)

### Caveats

* Tested only with GMail's IMAP. Should be used with other services and with SMTP, that should also work, probably.
* Only takes into account the first category of a feed. While both GMil and GReader allow a message/post to be assigned to multiple folders/labels, rss2imap assumes a single folder per message (as per IMAP's model).
* Doesn't keep track of each feed items it imports, so running multiple times will effectively produce duplicate messages. Use the --use-cache switch if you want to run multiple times over the same set of cache

### Suggestions to configure GMail as a feed reader

* Create a GMail account exclusively for your feed items
* Go to "settings > labs" and activate the "Preview Pane" extension
* Go to "settings > accounts > grant access to your account" and grant access from your main gmail account
* Go to "settings > inbox", activate "priority inbox", and add "unread" as the top section

## Next Steps

* Add memoization to images retrieved from archive.org (e.g., it keeps retrieving the same mugshot images over and over for old planet feeds/posts)
* When using GMail to import from GReader, use GMail's labels extension to create messages with multiple labels (related: check if GMail's labels extensions is faster than assigning messages to a folder)
* For imap-based delivery, add an option to change the meaning of "active" from "don't send mail" to "mark it automatically as read"
* Test nested folders (am only using single folders, not a nested hierarchy, so this might break)
* Automatic message categorization using Bayesian filtering and NLTK
* Better reference tracking to identify 'hot' items
* Figure out a nice way to do favicons (X-Face is obsolete, and so is X-Image-URL)
* Refactor this as a multi-threaded app with a SQLite feed store

Be aware that this works and is easy to hack, but uses old Python idioms and could do with some refactoring (PEP-8 zealots are sure to cringe as they read through the code).
