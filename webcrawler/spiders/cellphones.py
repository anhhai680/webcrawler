# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.spiders import SitemapSpider
from ..items import ProductItem

logger = logging.getLogger('cellphones_logger')

# class CellphonesSpider(SitemapSpider):


class CellphonesSpider(scrapy.Spider):
    name = 'cellphones'
    allowed_domains = ['cellphones.com.vn', 'hoanghamobile.com']
    #sitemap_urls = ['https://cellphones.com.vn/sitemap.xml']
    start_urls = [
        'https://cellphones.com.vn/mobile.html',
        'https://hoanghamobile.com/dien-thoai-di-dong-c14.html',
        # 'https://cellphones.com.vn/tablet.html',
        # 'https://cellphones.com.vn/hang-cu.html',
        # 'https://cellphones.com.vn/do-choi-cong-nghe/fitbit.html',
    ]

    def parse(self, response):
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
        paging_pages = response.xpath('//div[@class="paging"]/a[not(contains(@class,"current"))]/@href').getall()
        if len(paging_pages) > 0:
            for next_link in paging_pages:
                next_link = "https://hoanghamobile.com" % next_link
                yield response.follow(next_link, callback=self.parse_hoanghamobile)
                pass
        pass

    # Following product detail to scrape all information of each product
    def parse_product_detail(self, response):
        def extract_with_css(query):
            return response.css(query).get(default='').strip()

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

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

        # product_info = {
        #     'title': extract_with_css('h1::text'),
        #     'description': extract_with_xpath('//meta[@name="description"]/@content'),
        #     'price': extract_price(),
        #     'images': extract_product_gallery('div.product-image-gallery>img'),
        #     'link': response.url
        # }

        product_link = response.url
        # Continues scrape other product model's link on this page
        for other_model_link in response.css('div.linked>div>a::attr(href)'):
            if other_model_link is not None and other_model_link != product_link:
                yield response.follow(other_model_link, self.parse_product_detail)

        products = ProductItem()

        product_title = extract_with_css('h1::text')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
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
    
    def parse_hoanghamobile_product_detail(self,response):
        pass
