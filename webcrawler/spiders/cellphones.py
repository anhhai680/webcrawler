# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.spiders import SitemapSpider

logger = logging.getLogger('cellphones_logger')

#class CellphonesSpider(SitemapSpider):
class CellphonesSpider(scrapy.Spider):
    name = 'cellphones'
    allowed_domains = ['cellphones.com.vn']
    sitemap_urls = ['https://cellphones.com.vn/sitemap.xml']
    start_urls = [
        'https://cellphones.com.vn/mobile.html',
        'https://cellphones.com.vn/tablet.html',
        'https://cellphones.com.vn/mobile/hang-sap-ve.html',
        'https://cellphones.com.vn/laptop/mac.html',
        'https://cellphones.com.vn/laptop/mac/imac.html',
        'https://cellphones.com.vn/laptop/mac/macbook-pro.html',
        'https://cellphones.com.vn/hang-cu.html',
        'https://cellphones.com.vn/phu-kien.html',
        'https://cellphones.com.vn/tablet/apple-7.html',
        'https://cellphones.com.vn/mobile/samsung.html',
        'https://cellphones.com.vn/mobile/sony-5.html',
        'https://cellphones.com.vn/phu-kien/apple.html',
        'https://cellphones.com.vn/laptop/phu-kien.html',
        'https://cellphones.com.vn/phu-kien/phu-kien-uag.html',
        'https://cellphones.com.vn/phu-kien/bao-da-op-lung/samsung.html',
        'https://cellphones.com.vn/phu-kien/energizer/bao-da-op-lung.html',
        'https://cellphones.com.vn/phu-kien/phu-kien-joyroom-44.html',
        'https://cellphones.com.vn/phu-kien/bao-da-op-lung/sony.html',
        'https://cellphones.com.vn/phu-kien/energizer.html',
        'https://cellphones.com.vn/phu-kien/anker-43.html',
        'https://cellphones.com.vn/thiet-bi-am-thanh/loa/anker.html',
        'https://cellphones.com.vn/do-choi-cong-nghe/fitbit.html',
        'https://cellphones.com.vn/phu-kien/pin-du-phong/pin-sac-khong-day.html',
        'https://cellphones.com.vn/do-choi-cong-nghe/vong-tay-thong-minh.html',
        'https://cellphones.com.vn/phu-kien/apple/iphone-7-8.html',
        'https://cellphones.com.vn/phu-kien/sale.html',
        'https://cellphones.com.vn/phu-kien/phu-kien-spigen.html',
        'https://cellphones.com.vn/phu-kien/apple/iphone-7-7-plus.html',
        'https://cellphones.com.vn/laptop/phu-kien/cap-chuyen-doi-dau-chuyen-doi-macbook.html',
        'https://cellphones.com.vn/laptop/phu-kien/ban-phim-macbook.html',
        'https://cellphones.com.vn/phu-kien/sac-dien-thoai/sac/joyroom.html'
    ]

    def parse(self, response):
        # page = response.url.split("/")[-2]
        # filename = 'cps-%s.html' % page
        # with open(filename,'wb') as f:
        #     f.write(response.body)
        # self.log('Saved file' % filename)
        #logger.info('Parse url: %s',response.url)
        def extract_with_css(item, query):
            return item.css(query).get(default='').strip()

        for item in response.css('li.cate-pro-short'):
            scraped_info = {
                # item.css('h3::text').get(),
                'title': extract_with_css(item, 'h3::text'),
                'img': item.css('img').xpath('@src').get(),
                'old_price': extract_with_css(item, 'p.old-price>span::text'),
                'price': extract_with_css(item, 'p.special-price>span::text'),
                'gift': extract_with_css(item, 'p.gift-cont::text')
            }
            #yield self.write_to_file(scraped_info)
            yield scraped_info

        links = response.xpath(
            '//ul[@class="pagination"]/li[not(contains(@class,"active"))]/a/@href').getall()

        for next_page in links:
            if next_page is not None:
                yield response.follow(next_page, callback=self.parse)
        pass
    
    def write_to_file(self,content):
        filename = 'cellphones-%s.json'
        with open(filename,'wb') as f:
            f.write(content)
