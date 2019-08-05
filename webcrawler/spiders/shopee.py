# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
import time

from ..items import ProductItem

logger = logging.getLogger(__name__)


class ShopeeSpider(scrapy.Spider):
    name = 'shopeedata'
    allowed_domains = ['shopee.vn']
    # start_urls = [l.strip() for l in open('shopee_links.jl').readlines()]
    # start_urls = ['https://shopee.vn/smartphone-cat.84.1979.19042']
    start_urls = [
        'https://shopee.vn/api/v2/search_items/?by=relevancy&keyword=smartphone&limit=50&match_id=19042&newest=0&order=desc&page_type=search']
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'USER_AGENT': {
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:35.0) Gecko/20100101 Firefox/35.0',
        }
    }

    def __init__(self, limit_pages=None, *args, **kwargs):
        super(ShopeeSpider, self).__init__(*args, **kwargs)
        self.page_number = 0
        self.total_records = 0
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 500

    def parse(self, response):
        logger.info('Scrape Url: %s', response.url)
        json_data = json.loads(response.body, encoding='utf-8')
        if json_data is not None:
            items = json_data['items']
            if len(items) > 0:
                # Get itemid and shopid from items list
                product_link = 'https://shopee.vn/api/v2/item/get?itemid={}&shopid={}'
                data = [product_link.format(item['itemid'], item['shopid'])
                        for item in items]
                for url in data:
                    yield scrapy.Request(url, callback=self.parse_product_detail)

        # Make a next page link to continues scrape
        next_page_url = 'https://shopee.vn/api/v2/search_items/?by=relevancy&keyword=smartphone&limit=50&match_id=19042&newest={}&order=desc&page_type=search'
        if self.page_number <= self.limit_pages:
            self.total_records += 50
            next_page = next_page_url.format(self.total_records)
            logger.info('Next page: %s', next_page)
            yield scrapy.Request(next_page, callback=self.parse)
            self.page_number += 1
        pass

    def parse_product_detail(self, response):
        logger.info('Product Url: %s', response.url)
        try:
            json_data = json.loads(response.body, encoding='utf-8')
            if json_data is not None:
                item = json_data['item']
                if item is not None:
                    product_title = str(item['name']).strip()
                    product_desc = str(item['description']).strip()
                    product_price = str(item['price'])
                    product_swatchcolors = [{mod['name'], str(mod['price'])}
                                            for mod in item['models'] if item['models']]
                    image_link = 'https://cf.shopee.vn/file/{}'
                    product_images = [image_link.format(
                        src) for src in item['images'] if item['images']]
                    product_specifications = [{attr['name'], attr['value']}
                                              for attr in item['attributes'] if item['attributes']]
                    product_link = 'https://shopee.vn/{}-i.{}.{}'.format(
                        product_title, item['shopid'], item['itemid'])

                    products = ProductItem(
                        cid=1,  # 1: Smartphone
                        title=product_title,
                        description=product_desc,
                        price=product_price,
                        swatchcolors=product_swatchcolors,
                        specifications=product_specifications,
                        link=product_link,
                        images=product_images,
                        shop='shopee',
                        domain='shopee.vn',
                        body=''
                    )

                    yield products

        except json.JSONDecodeError as ex:
            logger.error('Could not parse json data. Errors %s' % ex)
        pass

    def parse_backup(self, response):
        logger.info('Scrape Url: %s', response.url)
        # links = response.xpath(
        #     '//div[@class="row shopee-search-item-result__items"]/div[@class="col-xs-2-4 shopee-search-item-result__item"]/div/a/@href').getall()
        links = response.xpath(
            '//div[@class="row shopee-search-item-result__items"]/div/div/a/@href').getall()
        logger.info('There is a total of ' + str(len(links)) + ' links')
        for product_link in links:
            try:
                product_link = "https://shopee.vn%s" % product_link
                yield response.follow(product_link, callback=self.parse_product_detail)
            except:
                pass

        time.sleep(1)

        next_page_url = response.xpath('//link[@rel="next"]/@href').get()
        logger.info('Next page: %s', next_page_url)
        if next_page_url is not None:
            match = re.match(r".*?page=(\d+)&", next_page_url)
            next_page_number = int(match.groups()[0])
            if next_page_number <= self.limit_pages:
                yield response.follow(next_page_url, callback=self.parse)
        else:
            logger.info('Next Page was not find on page %s', response.url)

    def parse_product_detail_backup(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            logger.info('Product Price: %s' % price)
            if price is not None:
                price = price.split('-')[0]
            return price

        logger.info('Parsing Url: %s', response.url)

        # Validate price with pattern
        # price_pattern = re.compile(r'(\S*[0-9](\w+?))')
        product_price = extract_price(
            '//div[contains(@class,"items-center")]/div[@class="_3n5NQx"]/text()')
        # logger.info('Product Price: %s' % product_price)
        if product_price is None or product_price == '':
            return

        product_title = extract_with_xpath('//div[@class="qaNIZv"]/text()')
        # product_desc = extract_with_xpath(
        #     '//div[@class="_2aZyWI"]/div[@class="_2u0jt9"]/span/text()')
        product_desc = response.css(
            'meta[name="description"]::attr("content")').get()
        product_swatchcolors = extract_xpath_all(
            '//div[@class="flex items-center crl7WW"]/button/text()')
        product_images = response.xpath(
            '//div[@class="_2MDwq_"]/div[@class="ZPN9uD"]/div[@class="_3ZDC1p"]/div/@style').re(r'(?:https?://).*?[^\)]+')

        # product_specifications
        product_specifications = []
        for item in response.xpath('//div[@class="_2aZyWI"]/div[@class="kIo6pj"]'):
            try:
                key = item.xpath(
                    './/label[not(contains(text(),"Danh Mục") or contains(text(),"Kho hàng") or contains(text(),"Gửi từ"))]/text()').get().strip()
                value = item.xpath('.//a/text() | .//div/text()').get().strip()
                product_specifications.append({key, value})
            except:
                pass

        # body = extract_with_xpath('//div[@class="_2u0jt9"]/span/text()')

        products = ProductItem(
            cid=1,  # 1: Smartphone
            title=product_title,
            description=product_desc,
            price=product_price,
            swatchcolors=product_swatchcolors,
            specifications=product_specifications,
            link=response.url,
            images=product_images,
            shop='shopee',
            domain='shopee.vn',
            body=''
        )

        yield products
