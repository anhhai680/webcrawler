# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.shell import inspect_response
from scrapy import signals

from ..items import ProductItem

logger = logging.getLogger(__name__)


class ShopeeSpider(CrawlSpider):
    custom_settings = {
        "DEPTH_LIMIT": 5,
        "DOWNLOAD_DELAY": 2,
    }
    name = 'shopee'
    allowed_domains = ['shopee.vn']
    start_urls = [
        'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=1&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=2&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=3&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=4&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=5&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=6&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=7&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=8&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=9&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=10&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=11&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=12&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=13&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=14&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=15&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=16&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=17&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=18&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=19&sortBy=pop',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979?page=20&sortBy=pop',
    ]
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/(.*?)-cat.84.1979',
                '/(.*?)-cat.84.1979?page=[0-9]&sortBy=pop'
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop/',
                '/khuyen-mai/',
            ),
        ), callback='parse_shopee'),
    )

    # @classmethod
    # def from_crawler(cls, crawler, *args, **kwargs):
    #     spider = super(ShopeeSpider, cls).from_crawler(
    #         crawler, *args, **kwargs)
    #     crawler.signals.connect(spider.spider_closed,
    #                             signal=signals.spider_closed)
    #     return spider

    # def spider_closed(self, spider):
    #     logger.info('Spider closed: %s', spider.name)

    def parse_shopee(self, response):
        logger.info('Page Url: %s', response.url)
        links = response.xpath(
            '//div[@class="row shopee-search-item-result__items"]/div[@class="col-xs-2-4 shopee-search-item-result__item"]/div/a/@href').getall()
        for product_link in links:
            product_link = "https://shopee.vn%s" % product_link
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        # pages = response.xpath(
        #     '//div[@class="shopee-page-controller"]/button/text()').getall()
        next_page = response.xpath('//link[@rel="next"]/@href').get()
        logger.info('Next Page: %s', next_page)
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_shopee)
        else:
            inspect_response(response, self)
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_with_xpath_by_item(query, item):
            return item.xpath(query).get(default='').strip()

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            return price

        logger.info('Product Url: %s', response.url)
        # Validate price with pattern
        price_pattern = re.compile(r'(\S*[0-9](\w+?))')
        # product_price = extract_price(
        #     '//div[@class="items-center"]/div[@class="_3n5NQx"]/text()')
        product_price = extract_price(
            '//div[contains(@class,"items-center")]/div[@class="_3n5NQx"]/text()')
        logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//div[@class="qaNIZv"]/text()')
        product_desc = extract_with_xpath(
            '//div[@class="_2aZyWI"]/div[@class="_2u0jt9"]/span/text()')
        product_swatchcolors = response.xpath(
            '//div[@class="flex items-center crl7WW"]/button/text()').getall()
        product_images = response.xpath(
            '//div[@class="_2MDwq_"]/div[@class="ZPN9uD"]/div[@class="_3ZDC1p"]/div/@style').re(r'background-image:url(.*?);')

        # product_specifications = response.xpath(
        #     '//table[@class="productSpecification_table"]/tbody/tr/td/text()').getall()
        product_specifications = []
        backlist = ('Danh Mục', 'Kho hàng', 'Gửi từ', 'Shopee')
        for item in response.xpath('//div[@class="_2aZyWI"]/div[@class="kIo6pj"]'):
            try:
                key = extract_with_xpath_by_item('.//label/text()', item)
                value = extract_with_xpath_by_item('.//a/text()', item)
                if (key == '' or value == '') or key in backlist:
                    break
                product_specifications.append({key, value})
            except:
                pass

        product_link = response.url
        products = ProductItem()
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = self.parse_money(product_price)
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images

        yield products

    def parse_money(self, value):
        return re.sub(r'[^\d.]', '', value)
