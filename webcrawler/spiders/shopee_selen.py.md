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
from selenium.common import exceptions

from ..items import ProductItem

logger = logging.getLogger(__name__)


class ShopeeSpider(scrapy.Spider):

    name = 'shopeeselen'
    allowed_domains = ['shopee.vn']
    # dowload_delay = 1
    start_urls = [
        'https://shopee.vn/Smartphone-%C4%90i%E1%BB%87n-tho%E1%BA%A1i-th%C3%B4ng-minh-cat.84.1979.19042',
        # 'https://shopee.vn/%C4%90i%E1%BB%87n-tho%E1%BA%A1i-cat.84.1979',
    ]
    # rules = (
    #     Rule(LxmlLinkExtractor(
    #         allow=(
    #             '/(.*?)-cat.84.1979',
    #             '/(.*?)-cat.84.1979?page=[0-9]&sortBy=pop'
    #         ),
    #         deny=(
    #             '/tin-tuc/',
    #             '/phu-kien/',
    #             '/huong-dan/',
    #             '/ho-tro/',
    #             '/tra-gop/',
    #             '/khuyen-mai/',
    #         ),
    #     ), callback='parse_shopee'),
    # )

    def __init__(self):
        options = webdriver.ChromeOptions()

        prefs = {'profile.managed_default_content_settings.images': 2}
        options.add_experimental_option('prefs', prefs)

        options.add_argument('headless')
        options.add_argument('--disable-images')
        options.add_argument('--disable-notifications')
        options.add_argument('--incognito')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-web-security')
        options.add_argument('--no-sandbox')

        self.driver = webdriver.Chrome(options=options)
        # self.driver.set_page_load_timeout(1)
        # self.driver.set_window_size(1120, 550)
        self.driver.wait = WebDriverWait(self.driver, 3)

    def parse(self, response):
        logger.info('Page Url: %s', response.url)

        self.driver.get(response.url)
        try:

            self.driver.wait.until(EC.presence_of_element_located(
                (By.XPATH, '//link[@rel="next"]/@href')))

            # using the JavaScriptExecutor to scroll down to bottom of window
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);")
            sleep(1)

        except:
            logger.info('link[@rel="next"] NOT FOUND IN TECHCRUNCH !!!')

        sel = Selector(text=self.driver.page_source)
        links = sel.xpath(
            '//div[@class="row shopee-search-item-result__items"]/div[@class="col-xs-2-4 shopee-search-item-result__item"]/div/a/@href').getall()

        logger.info('There is a total of ' + str(len(links)) + ' links')
        for product_link in links:
            try:
                product_link = "https://shopee.vn%s" % product_link
                yield response.follow(product_link, callback=self.parse_product_detail)
            except:
                pass

        # Following next page to scrape
        while True:
            try:
                next_page = self.driver.find_element_by_xpath(
                    '//link[@rel="next"]/@href')
                logger.info('Next page: %s', next_page)
                if next_page is not None:
                    # yield scrapy.Request(next_page, callback=self.parse)
                    next_page.click()
                else:
                    self.driver.close()
                    logger.info(
                        'Next Page could not found in page source %s', response.url)
            except:
                self.driver.close()
                logger.info('NEXT PAGE NOT FOUND(OR EOF) IM CLOSING MYSELF !!!')
                break

        self.driver.quit()

    def parse_product_detail(self, response):

        # try:
        #     self.driver.get(response.url)
        #     self.driver.wait.until(
        #         EC.presence_of_element_located(
        #             (By.XPATH, '//link[@rel="canonical"]/@href')
        #         )
        #     )
        # except exceptions.TimeoutException as e:
        #     logger.error(
        #         '{}: TimeoutException waiting for loaded page: {}'.format(response.url, e))
        # except exceptions.InvalidSelectorException as e:
        #     logger.error(
        #         '{}: InvalidSelectorException waiting for loaded page: {}'.format(response.url, e))

        # sel = Selector(text=self.driver.page_source)

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

        logger.info('Product Url: %s', response.url)
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
        #backlist = ('Danh Mục', 'Kho hàng', 'Gửi từ', 'Shopee')
        for item in response.xpath('//div[@class="_2aZyWI"]/div[@class="kIo6pj"]'):
            try:
                key = item.xpath('.//label/text()').get().strip()
                value = item.xpath('.//a/text() | .//div/text()').get().strip()
                # if (key == '' or value == '') or key in backlist:
                #     break
                product_specifications.append({key, value})
            except:
                logger.info('Item: %s', str(item))
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

    def parse_money(self, value):
        return re.sub(r'[^\d.]', '', value)
