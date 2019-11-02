#--- Function ti pull and parse rss feed
import ssl
import feedparser
from collections import defaultdict

def lambda_handler():
	if hasattr(ssl, '_create_unverified_context'):
		ssl._create_default_https_context = ssl._create_unverified_context

	full_feed_list = []

	sw_url = 'http://www.secureworks.com/rss?feed=research&category=advisories'
	this_sw_feed = feedparser.parse(sw_url)
#	sw_feed_dict = defaultdict(dict)

	for feed in this_sw_feed.entries:
		sw_feed_dict = {
				'title': feed.title,
				'summary': feed.summary,
				'link':  feed.link,
				'summaryDetail': feed.summary_detail.value
				}
		full_feed_list.append(sw_feed_dict)


	sans_url = 'https://isc.sans.edu/rssfeed_full.xml'
	this_sans_feed = feedparser.parse(sans_url)

	sans_feed_dict = {}

	for sans in this_sans_feed.entries:
		sans_feed_dict = {
				'title': sans.title,
				'summary': sans.summary,
				'link': sans.link,
				'summaryDetail': sans.summary_detail.value
				}
		full_feed_list.append(sans_feed_dict)

	return full_feed_list
