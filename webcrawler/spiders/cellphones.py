# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.spiders import SitemapSpider

logger = logging.getLogger('cellphones_logger')

# class CellphonesSpider(SitemapSpider):


class CellphonesSpider(scrapy.Spider):
    name = 'cellphones'
    allowed_domains = ['cellphones.com.vn']
    #sitemap_urls = ['https://cellphones.com.vn/sitemap.xml']
    start_urls = [
        'https://cellphones.com.vn/mobile.html',
        # 'https://cellphones.com.vn/tablet.html',
        # 'https://cellphones.com.vn/hang-cu.html',
        # 'https://cellphones.com.vn/do-choi-cong-nghe/fitbit.html',
    ]

    def parse(self, response):
        #logger.info('Parse url: %s',response.url)
        # def extract_with_css(item, query):
        #     return item.css(query).get(default='').strip()

        # def extract_price(item):
        #     price = item.css(
        #         'p.special-price>span::text').get(default='').strip()
        #     if price == '':
        #         price = item.css(
        #             'span.regular-price>span::text').get(default='').strip()
        #     return price

        for item in response.css('li.cate-pro-short'):
            # scraped_info = {
            #     'title': extract_with_css(item, 'h3::text'),
            #     'link': item.css('a').xpath('@href').get(),
            #     'img': item.css('img').xpath('@src').get(),
            #     'old_price': extract_with_css(item, 'p.old-price>span::text'),
            #     'price': extract_price(item),
            #     'gift': extract_with_css(item, 'p.gift-cont::text')
            # }
            # yield scraped_info
            link_product = item.css('a').xpath('@href').get()
            if link_product is not None:
                yield response.follow(link_product,self.parse_product_detail)

        links = response.xpath(
            '//ul[@class="pagination"]/li[not(contains(@class,"active"))]/a/@href').getall()

        for next_page in links:
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse)
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
        
        def extract_product_gallery(query):
            return response.css(query).xpath("@src").getall()

        product_info = {
            'title': extract_with_css('h1::text'),
            'description': extract_with_xpath('//meta[@name="description"]/@content'),
            'price': extract_price(),
            'images': extract_product_gallery('div.product-image-gallery>img'),
            'link': response.url
        }
        yield product_info
        pass
