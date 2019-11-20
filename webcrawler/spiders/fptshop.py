# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from ..items import ProductItem

logger = logging.getLogger(__name__)


class FptshopSpider(scrapy.Spider):
    name = 'fptshop'
    allowed_domains = ['fptshop.com.vn']
    start_urls = [
        'https://fptshop.com.vn/dien-thoai?sort=ban-chay-nhat',
    ]
    # rules = (
    #     Rule(LinkExtractor(
    #         allow=(
    #             '/dien-thoai/',
    #             '/dien-thoai/[\\w-]+/[\\w-]+$'
    #         ),
    #         deny=(
    #             '/tin-tuc/',
    #             '/ctkm/(.*?)',
    #             '/phu-kien/',
    #             '/huong-dan/',
    #             '/ho-tro/',
    #             '/tra-gop',
    #             '/kiem-tra-bao-hanh?tab=thong-tin-bao-hanh',
    #             '/cua-hang',
    #             '/kiem-tra-hang-apple-chinh-hang',
    #             '/ffriends',
    #             '/khuyen-mai',
    #             '/sim-so-dep',
    #             'tel:18006601',
    #             'tel:18006616'
    #         ),
    #         deny_domains=(
    #             'vieclam.fptshop.com.vn',
    #             'online.gov.vn',
    #             'hangmy.fptshop.com.vn'
    #         ),
    #     ), callback='parse_fptshop'),
    # )
    handle_httpstatus_list = [301, 302, 400]

    def __init__(self, limit_pages=None, *a, **kw):
        super(FptshopSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape url: %s' % response.url)
        for link in response.xpath('//div[@class="fs-lpil"]/a[@class="fs-lpil-img"]/@href').getall():
            product_link = "https://fptshop.com.vn%s" % link
            logger.info('Product Link %s' % product_link)
            yield response.follow(product_link, callback=self.parse_product_detail)

        next_page = response.xpath(
            '//div[@class="f-cmtpaging"]/ul/li[not(@class="active")]/a/@data-page').get()
        if next_page is not None:
            next_page_number = int(next_page)
            if next_page_number <= self.limit_pages:
                next_page = 'https://fptshop.com.vn/dien-thoai?sort=ban-chay-nhat&trang=%s' % next_page
                yield response.follow(next_page, callback=self.parse)
            else:
                logger.info('Spider will be stop here.{0} of {1}'.format(
                    next_page_number, next_page))
        pass

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        # Validate price with pattern
        price_pattern = re.compile("([0-9](\\w+ ?)*\\W+)")
        product_price = extract_with_xpath(
            '//div[contains(@class,"fs-pr-box")]/p[contains(@class,"fs-dtprice")]/text()')
        #logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return
        else:
            product_price = self.parse_money(product_price)

        product_title = extract_with_xpath('//h1[@class="fs-dttname"]/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_xpath_all(
            '//div[@class="fs-dticolor fs-dticolor-img"]/ul/li/span/@title')
        product_images = extract_xpath_all(
            '//div[@class="easyzoom"]/a/@href')

        #product_specifications = extract_xpath_all('//div[@class="fs-tsright"]/ul/li/*/text()')
        # product_specifications = []
        # for spec_row in response.xpath('//div[@class="fs-tsright"]/ul/li'):
        #     if spec_row is not None:
        #         try:
        #             spec_key = spec_row.xpath('.//label/text()').get().strip()
        #             spec_value = spec_row.xpath('.//span/text()').get().strip()
        #             product_specifications.append({spec_key, spec_value})
        #         except:
        #             pass
        product_specifications = []
        names = extract_xpath_all(
            '//div[@class="fs-tsright"]/ul/li/label/text()')
        values = extract_xpath_all(
            '//div[@class="fs-tsright"]/ul/li/span/text()')
        for index in range(len(names)):
            if values[index] is not None and values[index] != '':
                spec_name = str(names[index]).replace(':', '').strip()
                spec_value = str(values[index]).strip()
                product_specifications.append([spec_name, spec_value])

        product_oldprice = 0
        oldprice = extract_with_xpath(
            '//p[contains(@class,"fs-dtprice")]/del/text()')
        if oldprice is not None and oldprice != '':
            product_oldprice = self.parse_money(oldprice)
        else:
            product_oldprice = 0
        # logger.info('Oldprice: {0}, Price: {1}'.format(
        #     product_oldprice, product_price))

        product_internalmemory = extract_with_xpath(
            '//div[@class="fs-tsright"]/ul/li/label[contains(text(),"Bộ nhớ trong")]/../span/text()')
        product_brand = extract_with_xpath(
            '//ul[@class="fs-breadcrumb"]/li/a[contains(@onclick,"Product Detail")]/text()')
        product_shop = 'fptshop'

        product_rates = None
        reviews = extract_with_xpath('//div[@class="fs-dttrating"]//h5/text()')
        if reviews is not None and reviews != '':
            product_rates = reviews.split('/')[0]
            product_rates = product_rates.replace(',', '.')
        else:
            product_rates = 0

        product_location = 'Hồ Chí Minh'
        product_sku = None
        sku = extract_with_xpath(
            '//h1[@class="fs-dttname"]/span[@class="nosku"]/text()')
        if sku is not None:
            product_sku = str(sku[1:-1])

        product_instock = 1

        product_link = response.url

        products = ProductItem()
        products['cid'] = 'dienthoai'  # 1: Smartphone
        products['title'] = product_title
        products['description'] = product_desc
        products['oldprice'] = int(product_oldprice)
        products['price'] = int(product_price)
        products['swatchcolors'] = product_swatchcolors
        products['internalmemory'] = product_internalmemory
        products['specifications'] = product_specifications
        products['link'] = product_link
        products['images'] = product_images
        products['brand'] = product_brand
        products["shop"] = product_shop
        products['rates'] = float(product_rates)
        products['location'] = product_location
        products["domain"] = 'fptshop.com.vn'
        products['sku'] = product_sku
        products['instock'] = product_instock
        products['body'] = ''

        yield products

    def parse_money(self, value):
        try:
            if str(value).isdigit():
                return value
            return re.sub(r'[^\d]', '', str(value))
        except Exception as ex:
            logger.error('parse_money errors: %s' % ex)
