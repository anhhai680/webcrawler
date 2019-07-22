# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor

from ..items import ProductItem

logger = logging.getLogger(__name__)


class FptshopSpider(CrawlSpider):
    name = 'fptshop'
    allowed_domains = ['fptshop.com.vn']
    start_urls = [
        'https://fptshop.com.vn/dien-thoai?sort=ban-chay-nhat',
    ]
    rules = (
        Rule(LxmlLinkExtractor(
            allow=(
                '/dien-thoai/',
                '/dien-thoai/[\\w-]+/[\\w-]+$'
            ),
            deny=(
                '/tin-tuc/',
                '/ctkm/(.*?)',
                '/phu-kien/',
                '/huong-dan/',
                '/ho-tro/',
                '/tra-gop',
                '/kiem-tra-bao-hanh?tab=thong-tin-bao-hanh',
                '/cua-hang',
                '/kiem-tra-hang-apple-chinh-hang',
                '/ffriends',
                '/khuyen-mai',
                '/sim-so-dep',
                'tel:18006601',
                'tel:18006616'
            ),
            deny_domains=(
                'vieclam.fptshop.com.vn',
                'online.gov.vn',
                'hangmy.fptshop.com.vn'
            ),
        ), callback='parse_fptshop'),
    )
    handle_httpstatus_list = [301]

    def parse_fptshop(self, response):
        logger.info('Scrape url: %s' % response.url)
        for link in response.xpath('//div[@class="fs-lpil"]/a[@class="fs-lpil-img"]/@href').getall():
            product_link = "https://fptshop.com.vn%s" % link
            logger.info('Product Link %s' % product_link)
            yield response.follow(product_link, callback=self.parse_product_detail)

        next_page = response.xpath(
            '//div[@class="f-cmtpaging"]/ul/li[not(@class="active")]/a/@data-page').get()
        if next_page is not None:
            next_page = 'https://fptshop.com.vn/dien-thoai?sort=ban-chay-nhat&trang=%s' % next_page
            yield response.follow(next_page, callback=self.parse_fptshop)
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            return price

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_price(
            '//div[contains(@class,"fs-pr-box")]/p[contains(@class,"fs-dtprice")]/text()')
        #logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//h1[@class="fs-dttname"]/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_xpath_all(
            '//div[@class="fs-dticolor fs-dticolor-img"]/ul/li/span/@title')
        product_images = extract_xpath_all(
            '//div[@class="easyzoom"]/a/@href')

        #product_specifications = extract_xpath_all('//div[@class="fs-tsright"]/ul/li/*/text()')
        product_specifications = []
        for spec_row in response.xpath('//div[@class="fs-tsright"]/ul/li'):
            if spec_row is not None:
                try:
                    spec_key = spec_row.xpath('.//label/text()').get().strip()
                    spec_value = spec_row.xpath('.//span/text()').get().strip()
                    product_specifications.append({spec_key, spec_value})
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
        products["shop"] = 'fptshop'
        products["domain"] = 'fptshop.com.vn'

        yield products
