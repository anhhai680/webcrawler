from scrapy.utils.request import request_fingerprint
from w3lib.url import url_query_cleaner
from scrapy.dupefilters import RFPDupeFilter


class MyRFPDupeFilter(RFPDupeFilter):

    """A dupe filter that considers specific ids in the url"""

    def request_fingerprint(self, request):
        new_request = request.replace(url=url_query_cleaner(request.url))
        return request_fingerprint(new_request)
