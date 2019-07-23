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
    download_delay = 1
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
        logger.info('Scrape Url: %s' % response.url)
        try:
            pageData = re.findall(
                "<script>window.pageData=({.+?})</script>", response.body.decode("utf-8"), re.S)
            data = json.loads(pageData[0])
            if data is not None:
                for item in data["mods"]["listItems"]:
                    for product in self.parse_product_detail(item):
                        yield product

            # Follow the next page to scrape data
            next_page = response.xpath('//link[@rel="next"]/@href').get()
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse_lazada)
        except Exception as ex:
            logger.error(
                'Could not parse url {} with errros: {}'.format(response.url, ex))
        pass

    def parse_product_detail(self, item):
        #logger.info('Item: %s' % item)

        product_title = item["name"]
        #product_desc = [st.strip() for st in item["description"]]
        product_desc = ''.join(item["description"])
        product_price = item["price"]
        product_swatchcolors = []
        product_specifications = []
        product_link = item["productUrl"]
        product_images = [st["image"] for st in item["thumbs"]]

        products = ProductItem()
        products['cid'] = 1  # 1: Smartphone
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images
        products["shop"] = 'lazada'
        products["domain"] = 'lazada.vn'

        yield products
