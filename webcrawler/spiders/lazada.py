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
#from scrapy.loader import ItemLoader


from ..items import ProductLoader


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
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'webcrawler.middlewares.lazada.LazadaSpiderMiddleware': 543
        },
    }

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
            pageData = re.findall(
                "<script>window.pageData=({.+?})</script>", response.body.decode("utf-8"), re.M)
            if pageData is not None:
                data = json.loads(pageData[0])
                if data["mods"]["listItems"] is not None:
                    for item in data["mods"]["listItems"]:
                        #product_link = 'https:%s' % item['productUrl']
                        product_location = item['location']
                        # product_instock = str(item['inStock'])
                        # product_shipping = 0  # No freeshipping
                        # if 'alias' in item['icons']:
                        #     if item['icons']['alias'] == 'freeShipping':
                        #         product_shipping = 1  # Its freeshipping

                        rating_scope = item['ratingScore']

                        for thumb_item in item['thumbs']:
                            product_link = 'https:%s' % thumb_item['productUrl']
                            product_sku = thumb_item['sku']
                            skuId = thumb_item['skuId']
                            # add product item to ItemLoader
                            il = ProductLoader()
                            il.add_value('link', product_link)
                            il.add_value('location', product_location)
                            #il.add_value('freeshipping', product_shipping)
                            # il.add_value('instock', product_instock)
                            il.add_value('rates', rating_scope)
                            il.add_value('sku', product_sku)
                            yield scrapy.Request(product_link, callback=self.parse_product_detail, cb_kwargs={'product_item': il.load_item(), 'skuId': skuId})
                        time.sleep(1)

            else:
                logger.info('Parsed pageData has been failed.')

            # Follow the next page to scrape data
            next_page = response.xpath('//link[@rel="next"]/@href').get()
            if next_page is not None:
                match = re.match(r".*?page=(\d+)", next_page)
                if match is not None:
                    next_page_number = int(match.groups()[0])
                    # logger.info('next_page_number: %s', str(next_page_number))
                    if next_page_number <= self.limit_pages:
                        yield response.follow(next_page, callback=self.parse_lazada)
                    else:
                        logger.info('Spider will be stop here.{0} of {1}'.format(
                            next_page_number, next_page))

        except Exception as ex:
            logger.error(
                'Could not parse url {} with errros: {}'.format(response.url, ex))
        pass

    def parse_product_detail(self, response, product_item, skuId):

        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        logger.info('Product Url: %s' % response.url)

        try:
            product_title = extract_with_xpath(
                '//span[@class="breadcrumb_item_text"]/span/text()')
            product_desc = extract_with_css(
                'meta[name="description"]::attr(content)')
            #product_link = response.url
            product_oldprice = 0
            product_price = 0
            product_images = None
            product_swatchcolors = None
            product_internalmemory = None
            product_specifications = []
            product_brand = None
            product_shop = None
            #product_rates = None
            product_instock = 1  # In stock otherwise 0 is out of stock

            app = re.findall(r'app.run\((.+?)\)\;\n',
                             response.body.decode('utf-8'), re.S)
            if app is not None:
                json_data = json.loads(app[0])
                if isinstance(json_data, list) or len(json_data) > 0:
                    fields = json_data['data']['root']['fields']
                    if len(fields) > 0:
                        product_shop = fields['seller']['name']
                        #product_rates = fields['seller']['rate'] if 'rate' in fields['seller'] else '0'
                        product_brand = fields['product']['brand']['name']
                        # product images
                        product_images = [
                            'https:' + item['src'] for item in fields['skuGalleries'][skuId] if item['type'] == 'img']
                        # 'https:' + item['src'] for item in fields['skuGalleries']['0'] if item['type'] == 'img']

                        # if fields['productOption']['skuBase']['properties'][0]['name'] == 'Nhóm màu':
                        #     product_swatchcolors = [
                        #         item['name'] for item in fields['productOption']['skuBase']['properties'][0]['values'] if 'name' in item]

                        if fields['primaryKey']['skuNames'] is not None:
                            product_swatchcolors = fields['primaryKey']['skuNames'][0]
                            product_internalmemory = fields['primaryKey']['skuNames'][1]

                        # if fields['productOption']['skuBase']['properties'][1]['name'] == 'Khả năng lưu trữ':
                        #     product_internalmemory = [
                        #         item['name'] for item in fields['productOption']['skuBase']['properties'][1]['values'] if 'name' in item]

                        # product_specifications
                        # data_specs = fields['product']['highlights']
                        # sel = Selector(text=data_specs)
                        # if sel is not None:
                        #     product_specifications = sel.xpath(
                        #         '//ul/li/text()').getall()
                        data_specs = fields['specifications'][skuId]
                        if data_specs is not None:
                            # product_specifications = data_specs['features']
                            for item_name in data_specs['features']:
                                spec_name = item_name
                                spec_value = str(
                                    data_specs['features'][item_name])
                                product_specifications.append(
                                    [spec_name, spec_value])

                            # price
                            #data_prices = fields['skuInfos']['0']['price']
                        data_prices = fields['skuInfos'][skuId]['price']
                        product_price = data_prices['salePrice']['value']
                        if product_price is not None and product_price != '':
                            product_price = product_price/10

                        if 'originalPrice' in data_prices:
                            product_oldprice = data_prices['originalPrice']['value']
                            if product_oldprice is not None and product_oldprice != '':
                                product_oldprice = product_oldprice/10

                        stock = fields['skuInfos'][skuId]['stock']
                        if stock is not None:
                            if int(stock) > 0:
                                product_instock = 1
                            else:
                                product_instock = 0  # Out of stock
            else:
                logger.info('Could not found fields in json response.')

            il = ProductLoader(item=product_item)
            il.add_value('cid', 'dienthoai')
            il.add_value('title', product_title)
            il.add_value('description', product_desc)
            il.add_value('oldprice', product_oldprice)
            il.add_value('price', product_price)
            il.add_value('swatchcolors', product_swatchcolors)
            il.add_value('internalmemory', product_internalmemory)
            il.add_value('specifications', product_specifications)
            il.add_value('images', product_images)
            il.add_value('brand', product_brand)
            il.add_value('shop', product_shop)
            #il.add_value('rates', product_rates)
            il.add_value('instock', product_instock)
            il.add_value('domain', 'lazada.vn')
            il.add_value('body', '')

            yield il.load_item()

        except Exception as ex:
            logger.error(
                'Could not parse {}. Errors {}'.format(response.url, ex))
        pass

    def get_unique_links(self, links):
        links = np.unique(links)
        return [item for item in links if item not in self.unique_urls]

    def store_link(self, link):
        if link not in self.unique_urls:
            np.append(self.unique_urls, link)
