# -*- coding: utf-8 -*-
import scrapy
import logging
import re

from ..items import ProductItem

logger = logging.getLogger(__name__)


class ShopeeSpider(scrapy.Spider):
    name = 'shopee'
    allowed_domains = ['shopee.vn']
    start_urls = [
        'https://shopee.vn/Smartphone-%C4%90i%E1%BB%87n-tho%E1%BA%A1i-th%C3%B4ng-minh-cat.84.1979.19042']


    def parse(self, response):
        logger.info('Scrape Url: %s', response.url)
        links = response.xpath(
            '//div[@class="row shopee-search-item-result__items"]/div[@class="col-xs-2-4 shopee-search-item-result__item"]/div/a/@href').getall()
        logger.info('There is a total of ' + str(len(links)) + ' links')
        
        for product_link in links:
            try:
                product_link = "https://shopee.vn%s" % product_link
                yield response.follow(product_link, callback=self.parse_product_detail)
            except:
                pass

        next_page = response.xpath('//link[@rel="next"]/@href').get()
        logger.info('Next page: %s', next_page)
        if next_page is not None:
            yield scrapy.Request(next_page, callback=self.parse)
        else:
            logger.info('Next Page was not find on page %s', response.url)

        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            if price is not None:
                price = price.split('-')[0]
            return price

        # Validate price with pattern
        price_pattern = re.compile(r'(\S*[0-9](\w+?))')
        product_price = extract_price(
            '//div[contains(@class,"items-center")]/div[@class="_3n5NQx"]/text()')
        # logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//div[@class="qaNIZv"]/text()')
        product_desc = extract_with_xpath(
            '//div[@class="_2aZyWI"]/div[@class="_2u0jt9"]/span/text()')
        product_swatchcolors = extract_xpath_all(
            '//div[@class="flex items-center crl7WW"]/button/text()')
        product_images = response.xpath(
            '//div[@class="_2MDwq_"]/div[@class="ZPN9uD"]/div[@class="_3ZDC1p"]/div/@style').re(r'(?:https?://).*?[^\)]+')

        # product_specifications
        product_specifications = []
        #backlist = ['Danh Mục', 'Kho hàng', 'Gửi từ', 'Shopee']
        for item in response.xpath('//div[@class="_2aZyWI"]/div[@class="kIo6pj"]'):
            try:
                key = item.xpath('.//label/text()').get().strip()
                value = item.xpath('.//a/text() | .//div/text()').get().strip()
                # if (key == '' or value == '') or key in backlist:
                #     break
                product_specifications.append({key, value})
            except:
                pass

        product_link = response.url

        products = ProductItem()
        products['cid'] = 1  # 1: Smartphone
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images
        products['shop'] = 'shopee'
        products['domain'] = 'shopee.vn'
        products['body'] = ''

        yield products
