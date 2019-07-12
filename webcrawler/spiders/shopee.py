# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from datetime import datetime
from time import sleep
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.shell import inspect_response
from scrapy.selector import Selector

import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


from ..items import ProductItem

logger = logging.getLogger(__name__)


class ShopeeSpider(CrawlSpider):
    # custom_settings = {
    #     "DEPTH_LIMIT": 5,
    #     "DOWNLOAD_DELAY": 2,
    # }
    name = 'shopee'
    allowed_domains = ['shopee.vn']
    dowload_delay = 1
    start_urls = [
        'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979',
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

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument("--disable-notifications")
        options.add_argument("--incognito")
        options.add_argument("--disable-extensions")
        options.add_argument(" --disable-gpu")
        options.add_argument(" --disable-infobars")
        options.add_argument(" -–disable-web-security")
        options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(chrome_options=options)
        #self.driver.set_window_size(1120, 550)
        # self.driver = webdriver.Chrome("C:\Users\Daniel\Desktop\Sonstiges\chromedriver.exe")
        self.driver.wait = WebDriverWait(self.driver, 5)

    def parse_shopee(self, response):
        logger.info('Page Url: %s', response.url)
        self.driver.get(response.url)

        try:
            
            self.driver.wait.until(EC.presence_of_element_located(
                (By.XPATH, '//link[@rel="canonical"]/@href')))

        except TimeoutException:
            self.driver.close()
            print(" block-content NOT FOUND IN TECHCRUNCH !!!")

        links = response.xpath(
            '//div[@class="row shopee-search-item-result__items"]/div[@class="col-xs-2-4 shopee-search-item-result__item"]/div/a/@href').getall()
        for product_link in links:
            product_link = "https://shopee.vn%s" % product_link
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        # pages = response.xpath(
        #     '//div[@class="shopee-page-controller"]/button/text()').getall()
        try:
            next_page = response.xpath('//link[@rel="next"]/@href').get()
            logger.info('Next Page: %s', next_page)
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse_shopee)
            # else:
            #     inspect_response(response, self)
            # pass
        except TimeoutException:
            self.driver.close()
            logger.info('NEXT NOT FOUND(OR EOF) IM CLOSING MYSELF !!!')

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
                logger.info('Item: %s', str(item))
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
        products['last_updated'] = datetime.now()

        yield products

    def parse_money(self, value):
        return re.sub(r'[^\d.]', '', value)
