# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from scrapy.spidermiddlewares.httperror import HttpError
from urlparser import urlparser


from ..items import ProductItem

logger = logging.getLogger(__name__)


class CellphonesSpider(CrawlSpider):
    name = 'cellphones'
    allowed_domains = ['cellphones.com.vn']
    start_urls = [
        'https://cellphones.com.vn/mobile.html',
        # 'https://cellphones.com.vn/tablet.html',
        # 'https://cellphones.com.vn/hang-cu.html',
    ]
    rules = (
        Rule(LxmlLinkExtractor(allow=(
            'mobile.html',
            'mobile.html?p=[0-9]',
            'https://cellphones.com.vn/mobile/[\\w-]+/[\\w-]+$',
        ), deny=(
            'itel-it2123v.html',
            'dien-thoai-pho-thong.html',
            'timkiem.html',
            '/sforum/'
            'mobile.html#top',
        )), callback='parse_cellphones'),
    )

    def parse_cellphones(self, response):
        logger.info('Scrape url: %s' % response.url)
        # Get all product links on current page
        for link_product in response.css('div.lt-product-group-image>a::attr(href)'):
            if link_product is not None:
                yield response.follow(link_product, self.parse_product_detail)

        # Following to scrape for next page
        next_page = response.xpath(
            '//ul[@class="pagination"]/li[not(contains(@class,"active"))]/a/@href').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse_cellphones)
        pass

    # Following product detail to scrape all information of each product
    def parse_product_detail(self, response):

        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        def extract_price():
            price = response.css(
                'p.special-price>span::text').get(default='').strip()
            if price == '':
                price = response.css(
                    'span.regular-price>span::text').get(default='').strip()
            return price

        def extract_product_gallery():
            gallery = response.css(
                'div.product-image-gallery>img::attr(src)').getall()
            if len(gallery) <= 0:
                gallery = response.css(
                    'div.product-img-box>img::attr(src)').get()
            return gallery

        product_link = response.url

        # Continues scrape other product model's link on this page
        # for other_model_link in response.css('div.linked>div>a::attr(href)'):
        #     if other_model_link is not None and other_model_link != product_link:
        #         yield response.follow(other_model_link, self.parse_cellphones_product_detail)

        other_model_link = response.css('div.linked>div>a::attr(href)').get()
        if other_model_link is not None and other_model_link != product_link:
            yield response.follow(other_model_link, self.parse_product_detail)

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_price()
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//h1/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_xpath_all(
            '//label[@class="opt-label"]/span/text()')
        product_images = response.xpath(
            '//div[@id="product-more-images"]/div[@class="lt-product-more-image"]/a/@onclick').re(r'(https\S+)\'')
        #product_images = extract_product_gallery()
        logger.info('Gallery: {} of product link: {}'.format(
            product_images, product_link))

        # product_specifications = response.xpath(
        #     '//table[@id="tskt"]/tr/*/text()').re('(\\w+[^\n]+)')
        # Specifications product
        product_specifications = []
        for spec_row in response.xpath('//table[@id="tskt"]/tr'):
            if spec_row is not None:
                try:
                    spec_key = spec_row.xpath('.//td/text()').get().strip()
                    spec_value = spec_row.xpath('.//td/text()')[1].get().strip()
                    product_specifications.append({spec_key,spec_value})
                except:
                    pass

        products = ProductItem()
        products['cid'] = 1  # 1: Smartphone
        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images
        products["shop"] = 'cellphones'
        products["domain"] = 'cellphones.com.vn'

        yield products

    def extract_domain_name(self, response):
        parsed_uri = urlparser.urlparse(response.url)
        domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return domain
