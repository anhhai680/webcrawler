# -*- coding: utf-8 -*-
import scrapy
import json
import logging
import re
from dicttoxml import dicttoxml
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector,SelectorList



class LazadaSpider(CrawlSpider):
    name = 'lazada'
    allowed_domains = ['www.lazada.vn']
    start_urls = ['https://www.lazada.vn/dien-thoai-di-dong/xiaomi/']

    def parse(self, response):
        #pageData = re.findall("window.pageData=(.+?);\n",response.body.decode("utf-8"), re.S)
        #pageData = response.xpath('//script[contains(.,"window.pageData")]/text()').get()
        yield { 
            'data': response.xpath('//script[contains(.,"window.pageData")]/text()').get()
         }
        pass
