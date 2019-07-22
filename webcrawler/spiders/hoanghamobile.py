# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from urlparser import urlparser


from ..items import ProductItem

logger = logging.getLogger(__name__)


class HoanghamobileSpider(CrawlSpider):
    name = 'hoanghamobile'
    allowed_domains = ['hoanghamobile.com']
    start_urls = ['https://hoanghamobile.com/']

    def parse_hoanghamobile(self, response):

        logger.info('Parsing url: %s', response.url)

        for link_product in response.css('div.mosaic-block>a::attr(href)'):
            if link_product is not None:
                yield response.follow(link_product, self.parse_hoanghamobile_product_detail)

        # Following all pagingtation pages
        paging_pages = response.xpath(
            '//div[@class="paging"]/a[not(contains(@class,"current"))]/@href').getall()

        if len(paging_pages) > 0:
            for next_link in paging_pages:
                #domain_name = self.extract_domain_name
                next_link = 'https://hoanghamobile.com' + next_link
                yield response.follow(next_link, callback=self.parse_hoanghamobile)
                pass
        pass

    # Scrape product from hoanghamobile.com
    def parse_hoanghamobile_product_detail(self, response):

        # Defined all xpath product
        XPATH_PRODUCT_TITLE = '//title/text()'
        XPATH_PRODUCT_DESCRIPTION = '//meta[@name="description"]/@content'
        XPATH_PRODUCT_PRICE = '//div[contains(@class,"product-price")]/p/span/text()'
        XPATH_PRODUCT_SWATCHCOLORS = '//div[@class="list-color"]/ul/li/a[@class="color-quad"]/span/text()'
        XPATH_PRODUCT_IMAGES = '//meta[@itemprop="image"]/@content'
        #XPATH_PRODUCT_SPECIFICATIONS = '//div[@class="simple-prop"]'

        product_link = response.url

        product_title = self.extract_with_xpath(response, XPATH_PRODUCT_TITLE)
        product_desc = self.extract_with_xpath(
            response, XPATH_PRODUCT_DESCRIPTION)
        product_price = self.extract_with_xpath(response, XPATH_PRODUCT_PRICE)
        product_swatchcolors = response.xpath(
            XPATH_PRODUCT_SWATCHCOLORS).getall()
        product_images = self.extract_with_xpath(
            response, XPATH_PRODUCT_IMAGES)
        product_specifications = []

        # Specifications product
        for spec_info in response.css('div.simple-prop>p'):
            if spec_info is not None:
                try:
                    spec_key = self.extract_with_css(spec_info, 'label::text')
                    spec_value = self.extract_with_css(
                        spec_info, 'span>a::text')
                    product_specifications.append({spec_key, spec_value})
                except:
                    pass
        # if score is None:
                # 	raise ValueError('BOT FOUND!! Empty body returned')

        products = ProductItem()
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images

        yield products
    
    def extract_with_css(self, response, query):
        return response.css(query).get(default='').strip()

    def extract_with_xpath(self, response, query):
        return response.xpath(query).get(default='').strip()

    def extract_domain_name(self, response):
        parsed_uri = urlparser.urlparse(response.url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return domain
