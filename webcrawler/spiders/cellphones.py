# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from ..items import ProductItem

logger = logging.getLogger('cellphones_logger')


class CellphonesSpider(CrawlSpider):
    name = 'cellphones'
    allowed_domains = ['cellphones.com.vn', 'hoanghamobile.com']
    # sitemap_urls = ['https://cellphones.com.vn/sitemap.xml']
    start_urls = [
        'https://cellphones.com.vn/mobile.html',
        'https://hoanghamobile.com/dien-thoai-di-dong-c14.html',
        # 'https://cellphones.com.vn/tablet.html',
        # 'https://cellphones.com.vn/hang-cu.html',
        # 'https://cellphones.com.vn/do-choi-cong-nghe/fitbit.html',
    ]
    rules = (
        Rule(LinkExtractor(allow=('mobile\.html'), deny=(
            'timkiem\.html')), callback='parse_cellphones'),

        # Extract links matching 'item.php' and parse them with the spider's method parse_item
        Rule(LinkExtractor(allow=('dien-thoai-di-dong-c14\.html')),
             callback='parse_hoanghamobile')
    )

    def parse_cellphones(self, response):
        # logger.info('Parse url: %s',response.url)
        # Get all product links on current page
        for link_product in response.css('div.lt-product-group-image>a::attr(href)'):
            if link_product is not None:
                yield response.follow(link_product, self.parse_product_detail)

        # Following to scrape for next page
        links = response.xpath(
            '//ul[@class="pagination"]/li[not(contains(@class,"active"))]/a/@href').getall()
        if len(links) > 0:
            for next_page in links:
                yield response.follow(next_page, callback=self.parse)
        pass

    # Scrape product from hoanghamobile.com
    def parse_hoanghamobile(self, response):
        for link_product in response.css('div.mosaic-block>a::attr(href)'):
            if link_product is not None:
                yield response.follow(link_product, self.parse_hoanghamobile_product_detail)

        # Following all pagingtation pages
        paging_pages = response.xpath(
            '//div[@class="paging"]/a[not(contains(@class,"current"))]/@href').getall()
        if len(paging_pages) > 0:
            for next_link in paging_pages:
                next_link = "https://hoanghamobile.com" + next_link
                yield response.follow(next_link, callback=self.parse_hoanghamobile)
                pass
        pass

    # Following product detail to scrape all information of each product
    def parse_product_detail(self, response):

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
        for other_model_link in response.css('div.linked>div>a::attr(href)'):
            if other_model_link is not None and other_model_link != product_link:
                yield response.follow(other_model_link, self.parse_product_detail)

        products = ProductItem()

        product_title = self.extract_with_css(response, 'h1::text')
        product_desc = self.extract_with_xpath(
            response, '//meta[@name="description"]/@content')
        product_price = extract_price()
        product_swatchcolors = response.css(
            'label.opt-label>span::text').getall()
        product_images = extract_product_gallery()
        product_specifications = response.xpath(
            '//*[@id="tskt"]/tr/*/text()').re('(\w+[^\n]+)')

        products['title'] = product_title
        products['description'] = product_desc
        products['price'] = product_price
        products['swatchcolors'] = product_swatchcolors
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images

        yield products
        pass

    def parse_hoanghamobile_product_detail(self, response):

        # Defined all xpath product
        XPATH_PRODUCT_TITLE = '//title/text()'
        XPATH_PRODUCT_DESCRIPTION = '//meta[@name="description"]/@content'
        XPATH_PRODUCT_PRICE = '//div[contains(@class,"product-price")]/p/span/text()'
        XPATH_PRODUCT_SWATCHCOLORS = '//div[@class="list-color"]/ul/li/a[@class="color-quad"]/span/text()'
        XPATH_PRODUCT_IMAGES = '//meta[@itemprop="image"]/@content'
        #XPATH_PRODUCT_SPECIFICATIONS = '//div[@class="simple-prop"]'

        product_link = response.url

        # product_title = self.extract_with_css(response, 'title::text')
        # product_desc = self.extract_with_xpath(
        #     response, '//meta[@name="description"]/@content')
        # product_price = self.extract_with_css(
        #     response, 'div.product-price>p>span::text')
        # product_swatchcolors = response.css(
        #     'a.color-quad>span::text').getall()
        # product_images = self.extract_with_xpath(
        #     response, '//meta[@itemprop="image"]/@content')
        # product_specifications = response.xpath(
        #     '//div[@class="simple-prop"]/p/*/text()').getall()

        product_title = self.extract_with_xpath(response, XPATH_PRODUCT_TITLE)
        product_desc = self.extract_with_xpath(
            response, XPATH_PRODUCT_DESCRIPTION)
        product_price = self.extract_with_xpath(response, XPATH_PRODUCT_PRICE)
        product_swatchcolors = response.xpath(
            XPATH_PRODUCT_SWATCHCOLORS).getall()
        product_images = self.extract_with_xpath(
            response, XPATH_PRODUCT_IMAGES)
        product_specifications = {}

        # Specifications product
        for spec_info in response.css('div.simple-prop>p'):
            if spec_info is not None:
                try:
                    spec_key = self.extract_with_css(spec_info, 'label::text')
                    spec_value = self.extract_with_css(spec_info, 'span>a::text')
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
        pass

    def extract_with_css(self, response, query):
        return response.css(query).get(default='').strip()

    def extract_with_xpath(self, response, query):
        return response.xpath(query).get(default='').strip()
