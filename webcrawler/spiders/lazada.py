# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
import time
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.selector import Selector
import numpy as np


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
            ),
        ), callback='parse_lazada'),
    )
    # custom_settings = {
    #     'DEPTH_LIMIT': 3,
    # }

    def __init__(self, limit_pages=None, *args, **kwargs):
        super(LazadaSpider, self).__init__(*args, **kwargs)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300
        self.unique_urls = []

    def parse_lazada(self, response):
        logger.info('Scrape Url: %s' % response.url)
        try:
            links = re.findall(r'\"productUrl\":\"(.+?)\"\,',
                               response.body.decode('utf-8'), re.S)
            # pageData = re.findall(
            #     "<script>window.pageData=({.+?})</script>", response.body.decode("utf-8"), re.M)
            if links is not None:
                # data = json.loads(pageData[0])
                # if data["mods"]["listItems"] is not None:
                links = np.unique(links)
                if len(links) > 0:
                    # for item in data["mods"]["listItems"]:
                    for link in links:
                        product_link = 'https:%s' % link

                        # # add product item to ItemLoader
                        # il = ProductLoader(item=ProductItem())
                        # #il.default_output_processor = Join()
                        # il.add_value('cid', cid)
                        # il.add_value('title', product_title)
                        # #il.add_value('description', product_desc)
                        # il.add_value('price', product_price)
                        # il.add_value('link', product_link)
                        # il.add_value('images', product_images)
                        # il.add_value('shop', 'lazada')
                        # il.add_value('domain', 'lazada.vn')
                        # il.add_value('body', '')

                        yield response.follow(product_link, callback=self.parse_product_detail)
                        time.sleep(1)

            else:
                logger.info('Parsed pageData has been failed.')

            # Follow the next page to scrape data
            next_page = response.xpath('//link[@rel="next"]/@href').get()
            match = re.match(r".*?page=(\d+)", next_page)
            next_page_number = int(match.groups()[0])
            # logger.info('next_page_number: %s', str(next_page_number))
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

    def parse_product_detail(self, response):

        def extract_with_css(query):
            return response.css(query).get().strip()

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        logger.info('Product Url: %s' % response.url)

        # il = ProductLoader(item=product_item)

        try:
            product_title = extract_with_xpath(
                '//span[@class="breadcrumb_item_text"]/span/text()')
            product_desc = extract_with_css(
                'meta[name="description"]::attr(content)')
            product_link = response.url
            product_price = None
            product_images = None
            product_swatchcolors = None
            product_specifications = None
            product_brand = None
            product_shop = None
            product_rates = None

            app = re.findall(r'app.run\((.+?)\)\;\n',
                             response.body.decode('utf-8'), re.S)
            if app is not None:
                json_data = json.loads(app[0])
                if isinstance(json_data, list) or len(json_data) > 0:
                    fields = json_data['data']['root']['fields']
                    if len(fields) > 0:
                        product_shop = fields['seller']['name']
                        product_rates = fields['seller']['rate'] if 'rate' in fields['seller'] else '0'
                        product_brand = fields['product']['brand']['name']
                        product_images = [
                            'https:' + item['src'] for item in fields['skuGalleries']['0'] if item['type'] == 'img']
                        product_swatchcolors = [
                            item['name'] for item in fields['productOption']['skuBase']['properties'][0]['values']]
                        # product_specifications
                        data_specs = fields['product']['highlights']
                        sel = Selector(text=data_specs)
                        if sel is not None:
                            product_specifications = sel.xpath(
                                '//ul/li/text()').getall()
                        # price
                        data_prices = fields['skuInfos']['0']['price']
                        product_price = data_prices['salePrice']['value']
                        if int(product_price) <= 0:
                            product_price = data_prices['originalPrice']['value']
                        product_price = product_price/10
            else:
                logger.info('Could not found fields in json response.')

            products = ProductItem(
                cid=1,  # 1: Smartphone
                title=product_title,
                description=product_desc,
                price=product_price,
                swatchcolors=product_swatchcolors,
                specifications=product_specifications,
                link=product_link,
                images=product_images,
                shop=product_shop,
                rates=product_rates,
                brand=product_brand,
                domain='lazada.vn',
                body=''
            )

            yield products

        except Exception as ex:
            logger.error('Could not parse skuBase selector. Errors %s', ex)
        pass

    def get_unique_links(self, links):
        links = np.unique(links)
        return [item for item in links if item not in self.unique_urls]

    def store_link(self, link):
        if link not in self.unique_urls:
            np.append(self.unique_urls, link)
