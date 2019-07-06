# -*- coding: utf-8 -*-
import scrapy


class HnammobileSpider(scrapy.Spider):
    name = 'hnammobile'
    allowed_domains = ['www.hnammobile.com']
    start_urls = ['http://www.hnammobile.com/']

    def parse(self, response):
        pass
