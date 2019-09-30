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


class TikiSpider(CrawlSpider):
    name = 'tiki'
    allowed_domains = ['tiki.vn']
    start_urls = ['https://tiki.vn/dien-thoai-smartphone/c1795?src=tree']
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/dien-thoai-smartphone/',
                '/dien-thoai-smartphone/[\\w-]+/[\\w-]+$'
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop/',
                '/khuyen-mai/',
                '/tel:19006035',
                '/tel:18006963',
                '/top/',
                '/dat-ve-may-bay?src=(.*?)',
                '/chuong-trinh/',
                '/phieu-qua-tang/'
                '/deal-hot?src=(.*?)'
            ),
        ), callback='parse_tiki'),
    )

    def parse_tiki(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.xpath('//div[@class="product-box-list"]/div/a/@href').getall():
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        # next_page = response.xpath(
        #     '//div[@class="list-pager"]/ul/li/a/@href').get()
        next_page = response.xpath(
            '//link[@rel="next"]/@href').get()
        if next_page is not None:
            #next_page = "https://tiki.vn%s" % next_page
            yield response.follow(next_page, callback=self.parse_tiki)
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        # # Validate price with pattern
        # price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        # # product_price = extract_price(
        # #     '//div[@class="price-block show-border"]/p[@class="special-price-item"]/span[@id="span-price"]/text()')
        # product_price = extract_with_xpath(
        #     '//span[@id="span-price"]/text()')
        # #logger.info('Product Price: %s' % product_price)
        # if re.match(price_pattern, product_price) is None:
        #     return

        # product_link = extract_with_xpath(
        #     '//meta[@property="og:url"]/@content')
        product_link = response.url
        product_title = extract_with_xpath(
            '//h1[@class="item-name"]/span/text()')
        product_desc = extract_xpath_all(
            '//div[@class="top-feature-item bullet-wrap"]/p/text()')
        product_desc = ''.join(product_desc)
        # product_swatchcolors = extract_swatchcolors(
        #     '//div[@class="product_pick_color"]/div[contains(@class,"prco_content")]/div[contains(@class,"color color_cover")]/a//text()')

        product_sku = extract_with_xpath('//div[@id="product-sku"]/p/text()')
        product_price = 0
        product_oldprice = extract_with_xpath(
            '//p[@id="p-listpirce"]/@data-value')
        product_images = None
        product_swatchcolors = None
        product_internalmemory = None
        product_specifications = None
        product_brand = extract_with_xpath(
            '//div[@class="item-brand"]/p/a/text()')
        product_shop = extract_with_xpath(
            '//div[@class="current-seller"]/div/div/span/text()')
        product_location = None
        product_shipping = None
        product_rates = None
        product_instock = 1  # Product in stock

        # product_images = extract_xpath_all(
        #     '//img[@class="product-magiczoom"]/@src')

        # if len(product_images) <= 0:
        #     product_images = extract_xpath_all(
        #         '//img[@class="product-magiczoom"]/@src')

        # product_images = extract_product_gallery(
        #     '//ul[@class="nk-product-bigImg"]/li/div[@class="wrap-img-tag-pdp"]/span/img/@src')

        # Specifications product
        product_specifications = extract_xpath_all(
            '//table[@id="chi-tiet"]/tbody/tr/td/text()')

        # product_specifications = []
        # for spec_row in response.xpath('//table[@id="chi-tiet"]/tbody'):
        #     if spec_row is not None:
        #         try:
        #             spec_values = spec_row.xpath('.//tr//text()').getall()
        #             spec_info = [st.strip() for st in spec_values]
        #             product_specifications.append({spec_info})
        #         except:
        #             pass

        # parse json data from response
        script = response.xpath(
            '//script/text()').re('var configuration = ({.*?});')
        if len(script) > 0:
            json_data = json.loads(script[0])
            if len(json_data) > 0:
                # if len(json_data["configurable_options"]) > 0:
                #     product_swatchcolors = [
                #         color["label"] for color in json_data["configurable_options"][0]["values"]]
                if len(json_data["configurable_products"]) > 0:
                    for item in json_data["configurable_products"]:
                        product_title = item['name']
                        product_price = item['price']
                        product_images = [img["large_url"]
                                          for img in item["images"]]
                        inventory_status = item['inventory_status']
                        if inventory_status is not None:
                            if inventory_status == 'available':
                                product_instock = 1
                            else:
                                product_instock = 0  # Out of stock
                        product_swatchcolors = [item['option1']]
                        spid = item['id']
                        product_link = re.sub(
                            r'spid=(.*)', 'spid=%s' % spid, product_link)

                        products = ProductItem()
                        products['cid'] = 'dienthoai'  # 1: Smartphone
                        products['title'] = product_title
                        products['description'] = product_desc
                        products['oldprice'] = product_oldprice
                        products['price'] = product_price
                        products['swatchcolors'] = product_swatchcolors
                        products['internalmemory'] = product_internalmemory
                        products['specifications'] = product_specifications
                        products['link'] = product_link
                        products['images'] = product_images
                        products['brand'] = product_brand
                        products['shop'] = product_shop
                        products['rates'] = product_rates
                        products['location'] = product_location
                        products['domain'] = 'tiki.vn'
                        products['sku'] = product_sku
                        products['instock'] = product_instock
                        products['shipping'] = product_shipping
                        products['body'] = ''

                        yield products
