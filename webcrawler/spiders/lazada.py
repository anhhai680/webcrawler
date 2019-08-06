# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
import time
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
from scrapy.loader import ItemLoader


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
                '/dien-thoai-di-dong/?page=[0-9]'
                # '/dien-thoai-di-dong/[\\w-]+/[\\w-]+$'
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

    def __init__(self, limit_pages=None, *args, **kwargs):
        super(LazadaSpider, self).__init__(*args, **kwargs)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 200

    def parse_lazada(self, response):
        logger.info('Scrape Url: %s' % response.url)
        try:
            pageData = re.findall(
                "<script>window.pageData=({.+?})</script>", response.body.decode("utf-8"), re.S)
            data = json.loads(pageData[0])
            if data is not None:
                if data["mods"]["listItems"] is not None:
                    for item in data["mods"]["listItems"]:
                        product_link = 'https:%s' % item["productUrl"]
                        for product in self.parse_item(item):
                            yield scrapy.Request(product_link, callback=self.parse_product_detail, meta={'product_item': product})

            time.sleep(1)
            # Follow the next page to scrape data
            next_page = response.xpath('//link[@rel="next"]/@href').get()
            match = re.match(r".*?page=(\d+)", next_page)
            next_page_number = int(match.groups()[0])
            if next_page_number <= self.limit_pages:
                if next_page is not None:
                    yield response.follow(next_page, callback=self.parse_lazada)
                else:
                    logger.info(
                        'Next page not found. Spider will be stop right now !!!')
        except Exception as ex:
            logger.error(
                'Could not parse url {} with errros: {}'.format(response.url, ex))
        pass

    def parse_item(self, item):

        # logger.info('Item: %s' % item)
        product_title = item["name"]
        # product_desc = [st.strip() for st in item["description"]]
        product_desc = ''.join(item["description"])
        product_price = item["price"]
        product_swatchcolors = []
        product_specifications = []
        product_link = item["productUrl"]
        product_images = [st["image"]
                          for st in item["thumbs"] if item['thumbs']]

        products = ProductItem(
            cid=1,  # 1: Smartphone
            title=product_title,
            description=product_desc,
            price=product_price,
            swatchcolors=product_swatchcolors,
            specifications=product_specifications,
            link=product_link,
            images=product_images,
            shop='lazada',
            domain='lazada.vn',
            body=''
        )

        return products

    def parse_product_detail(self, response):
        logger.info('Product Url: %s' % response.url)

        product_item = response.meta['product_item']
        product_swatchcolors = None
        product_specifications = None

        try:
            data_swatch = re.findall(r'.*?skuBase\":({.+?})\}\,',
                                     response.body.decode('utf-8'), re.S)
            json_data = json.loads(data_swatch[0], encoding='utf-8')
            if json_data is not None:
                product_swatchcolors = [item['name'] for item in json_data['properties']
                                        [0]['values'] if json_data['properties'][0]['values']]
        except Exception as ex:
            logger.error('Could not parse skuBase selector. Errors %s', ex)

        try:
            data_specs = re.findall(r'.*?highlights\":\"(.+?)\"\,',
                                    response.body.decode('utf-8'), re.S)
            sel = Selector(text=data_specs[0])
            product_specifications = sel.xpath('//ul/li/text()').getall()
        except Exception as ex:
            logger.error('Could not parse highlights selector. Errors %s', ex)

        # products = ProductItem(
        #     swatchcolors=product_swatchcolors,
        #     specifications=product_specifications,
        #     shop='lazada',
        #     domain='lazada.vn',
        #     body=''
        # )
        product_item['swatchcolors'] = product_swatchcolors
        product_item['product_specifications'] = product_specifications

        yield product_item
