# -*- coding: utf-8 -*-
import requests
def get_file(url, agent=None, referer=None):
    wbm_url = "http://web.archive.org/web/form-submit.jsp?type=replay&url={0}".format(url)

    headers = {}
    if agent:
        headers['User-Agent'] = agent
    if referer:
        headers['Referer'] = referer
    resp = requests.get(wbm_url, headers=headers)
    if resp.status_code != 200:
        raise Exception("Unable to retrieve from waybackmachine: {0}".format(url))
    return (resp.headers, resp.content)
