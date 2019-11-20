# -*- coding: utf-8 -*-
import scrapy
import logging
import re
import json
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ..items import ProductItem

logger = logging.getLogger(__name__)


class HnammobileSpider(scrapy.Spider):
    name = 'hnammobile'
    allowed_domains = ['www.hnammobile.com']
    start_urls = ['https://www.hnammobile.com/dien-thoai/']
    # rules = (
    #     Rule(LinkExtractor(
    #         allow=('/dien-thoai/'),
    #         deny=(
    #             '/dien-thoai/#',
    #             '/tin-tuc/',
    #             '/may-tinh-bang/',
    #             '/phu-kien/',
    #             '/dong-ho-thong-minh/',
    #             '/kho-sim',
    #             '/event/',
    #             '/loai-dien-thoai/',
    #             '/mua-tra-gop',
    #             'https://www.hnammobile.com/dien-thoai/tel:19002012',
    #             'https://www.hnammobile.com/dien-thoai/tel:01234303000'
    #         )
    #     ), callback='parse_hnammobile'),
    # )
    handle_httpstatus_list = [301, 302]

    def __init__(self, limit_pages=None, *a, **kw):
        super(HnammobileSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.css('div.image>a::attr(href)'):
            yield response.follow(product_link, callback=self.parse_product_detail)

        # following pagination next page to scrape
        # links = response.xpath(
        #     '//li[contains(@class,"pagination-item") and (not(contains(@class,"active")))]/a/@href').getall()
        # if len(links) > 0:
        #     for next_page in links:
        #         yield response.follow(next_page, callback=self.parse_hnammobile)
        next_page = response.xpath(
            '//li[contains(@class,"pagination-item") and (not(contains(@class,"active")))]/a/@href').get()
        if next_page is not None:
            match = re.match(r".*?page=(\d+)", next_page)
            if match is not None:
                next_page_number = int(match.groups()[0])
                if next_page_number <= self.limit_pages:
                    yield response.follow(next_page, callback=self.parse)
                else:
                    logger.info('Spider will be stop here.{0} of {1}'.format(
                        next_page_number, next_page))
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_with_xpath(
            '//h3[contains(@class,"price")]/font/font[@class="numberprice"]/text()')
        if re.match(price_pattern, product_price) is None:
            return
        else:
            product_price = self.parse_money(product_price)

        product_title = extract_with_xpath('//h2[@class="title"]/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_xpath_all(
            '//div[@class="picker-color row"]/ul/li/img/@data-title')
        product_images = extract_xpath_all(
            '//div[@class="gallery"]//div[contains(@class,"item")]/@data-src')

        #product_specifications = response.xpath('//div[@class="content-body"]/div[@class="row size-screen"]//text()').getall()
        # product_specifications = []
        # for spec_row in response.xpath('//div[@class="content-body"]/div'):
        #     if spec_row is not None:
        #         try:
        #             spec_key = spec_row.xpath('.//label/text()').get().strip()
        #             spec_value = spec_row.xpath('.//p/text()').get().strip()
        #             product_specifications.append({spec_key, spec_value})
        #         except:
        #             pass

        product_specifications = []
        names = extract_xpath_all(
            '//div[@class="content-body"]/div/label/text()')
        values = extract_xpath_all(
            '//div[@class="content-body"]/div/p/text()')
        for index in range(len(names)):
            if values[index] is not None and values[index] != '':
                product_specifications.append([names[index], values[index]])

        product_oldprice = 0
        product_internalmemory = extract_with_xpath(
            '//div[@class="content-body"]/div/label[contains(text(),"Bộ nhớ trong")]/../p/text()')
        product_brand = None
        product_shop = 'Hnammobile'
        product_rates = 0
        product_location = 'Hồ Chí Minh'
        product_sku = None
        product_instock = 1

        jsondata = response.xpath(
            '//script[@type="application/ld+json"]/text()')[1].get()
        if jsondata is not None:
            data = json.loads(jsondata)
            if len(data) > 0:
                if 'brand' in data:
                    product_brand = str(data['brand'])
                if 'sku' in data:
                    product_sku = str(data['sku'])
                if len(data['offers']) > 0:
                    product_oldprice = self.parse_money(
                        data['offers']['highPrice'])
                    product_price = self.parse_money(
                        data['offers']['lowPrice'])
                    availability = data['offers']['availability']
                    if availability != 'InStock':
                        product_instock = 0  # Out of stock

        product_link = response.url
        products = ProductItem()
        products['cid'] = 'dienthoai'  # 1: Smartphone
        products['title'] = product_title
        products['description'] = product_desc
        products['oldprice'] = int(product_oldprice)
        products['price'] = int(product_price)
        products['swatchcolors'] = product_swatchcolors
        products['internalmemory'] = product_internalmemory
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images
        products['brand'] = product_brand
        products["shop"] = product_shop
        products['rates'] = float(product_rates)
        products['location'] = product_location
        products["domain"] = 'hnammobile.com'
        products['sku'] = product_sku
        products['instock'] = product_instock
        products['body'] = ''

        yield products

    def parse_money(self, value):
        try:
            if str(value).isdigit():
                return value
            return re.sub(r'[^\d]', '', str(value))
        except Exception as ex:
            logger.error('parse_money errors: %s' % ex)
