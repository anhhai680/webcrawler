# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from datetime import datetime


class SendoSpider(CrawlSpider):
    name = 'sendo'
    allowed_domains = ['www.sendo.vn']
    start_urls = [
        'https://www.sendo.vn/smartphone/',
        'https://www.sendo.vn/iphone/'
    ]

    def parse(self, response):
        pass
