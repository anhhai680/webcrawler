# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from datetime import datetime


from ..items import ProductItem

logger = logging.getLogger(__name__)


class LazadaSpider(CrawlSpider):
    name = 'lazada'
    allowed_domains = ['www.lazada.vn']
    start_urls = ['https://www.lazada.vn/dien-thoai-di-dong/']
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/dien-thoai-di-dong/',
                '/dien-thoai-di-dong/[\\w-]+/[\\w-]+$'
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop/',
                '/khuyen-mai/',
                '/tui-deo-cheo-deo-vai-nu/',
                '/pages/i/vn/digitalgoods/voucher-dich-vu',
                '/wow/camp/vn/midyear-festival/voucher',
                '/helpcenter/'
                '/about/',
                '/sell-on-lazada/',
                '/affiliate/',
                '/press/'
            ),
            deny_domains=(
                'pages.lazada.vn'
            )
        ), callback='parse_lazada'),
    )

    def parse_lazada(self, response):
        #pattern = re.compile(r'window.pageData=({.*?})', re.MULTILINE)
        #pageData = response.xpath('//script[contains(.,"window.pageData")]/text()').get()
        pageData = re.findall(
            "<script>window.pageData=({.+?})</script>", response.body.decode("utf-8"), re.S)
        data = json.loads(pageData[0])
        if data is not None:
            for item in data["mods"]["listItems"]:
                for product in self.parse_product_detail(item):
                    yield product
        pass

    def parse_product_detail(self, item):
        logger.info('Item: %s' % item)
        product_title = item["name"]
        product_desc = [st.strip() for st in item["description"]]
        product_price = item["priceShow"]
        product_swatchcolors = []
        product_specifications = ''
        product_link = item["productUrl"]
        product_images = [st["image"] for st in item["thumbs"]]

        products = ProductItem()
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images
        products['last_updated'] = datetime.now()
        yield products
