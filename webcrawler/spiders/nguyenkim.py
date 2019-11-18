# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor


from ..items import ProductItem

logger = logging.getLogger(__name__)


class NguyenkimSpider(scrapy.Spider):
    name = 'nguyenkim'
    allowed_domains = ['www.nguyenkim.com']
    start_urls = ['https://www.nguyenkim.com/dien-thoai-di-dong/']
    #download_delay = 1
    # rules = (
    #     Rule(LinkExtractor(
    #         allow=(
    #             '/dien-thoai-di-dong/',
    #             '/dien-thoai-di-dong/[\\w-]+/[\\w-]+$'
    #         ),
    #         deny=(
    #             '/tin-tuc/',
    #             '/phu-kien/',
    #             '/huong-dan/',
    #             '/ho-tro/',
    #             '/tra-gop/',
    #             'https://www.nguyenkim.com/cac-trung-tam-mua-sam-nguyen-kim.html',
    #             '/khuyen-mai/',
    #             'https://www.nguyenkim.com/dien-thoai-di-dong/?sort_by=position&sort_order=desc',
    #             'https://www.nguyenkim.com/dien-thoai-di-dong/?type_load=listing',
    #             'https://www.nguyenkim.com/dien-thoai-di-dong/?features_hash=(.*?)'
    #         ),
    #     ), callback='parse_nguyenkim'),
    # )

    handle_httpstatus_list = [301, 302]

    def __init__(self, limit_pages=None, *a, **kw):
        super(NguyenkimSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape url: %s' % response.url)

        # for product_link in response.xpath('//div[@class="item nk-fgp-items"]/a[@class="nk-link-product"]/@href').getall():
        #     yield response.follow(product_link, callback=self.parse_product_detail)
        for product_link in response.xpath('//div[@id="pagination_contents"]/div[@class="item nk-fgp-items nk-new-layout-product-grid"]/a[@class="nk-link-product"]/@href'):
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        # next_page = response.xpath(
        #     '//div[@class="NkPaging ty-pagination__items"]/a/@href').get()
        next_page = response.xpath('//link[@rel="next"]/@href').get()
        if next_page is not None:
            match = re.match(r".*/page-(\d+)", next_page)
            if match is not None:
                next_page_number = int(match.groups()[0])
                if next_page_number <= self.limit_pages:
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
            '//div[@class="product_info_price_value-final"]/span[@class="nk-price-final"]/text()')
        #logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return
        else:
            product_price = self.parse_money(product_price)

        product_title = extract_with_xpath(
            '//h1[@class="product_info_name"]/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_xpath_all(
            '//div[@class="product_pick_color"]/div[@class="prco_label" and contains(text(),"Màu sắc:")]/../div[contains(@class,"prco_content")]/div/a/@title')
        # product_images = extract_xpath_all(
        #     '//ul[@class="nk-product-bigImg"]/li/div[@class="wrap-img-tag-pdp"]/span/img/@src')
        product_images = extract_xpath_all(
            '//div[@class="nk-product-total"]/ul/li/img/@data-full | //div[@class="nk-product-total"]/li/img/@data-full')

        # product_specifications = response.xpath(
        #     '//table[@class="productSpecification_table"]/tbody/tr/td/text()').getall()
        product_specifications = []
        names = extract_xpath_all(
            '//table[@class="productSpecification_table"]/tbody/tr/td[1]/text()')
        values = extract_xpath_all(
            '//table[@class="productSpecification_table"]/tbody/tr/td[2]/text()')
        for index in range(len(names)):
            if values[index] is not None and values[index] != '':
                spec_name = str(names[index]).replace(':', '').strip()
                spec_value = str(values[index]).strip()
                product_specifications.append([spec_name, spec_value])

        product_oldprice = 0
        oldprice = extract_with_xpath(
            '//div[@class="product_info_price_value-real"]/span/text()')
        if oldprice is not None and oldprice != '':
            product_oldprice = self.parse_money(oldprice)
        else:
            product_oldprice = 0

        product_internalmemory = extract_with_xpath(
            '//table[@class="productSpecification_table"]/tbody/tr/td[contains(text(),"Bộ nhớ trong")]/../td[@class="value"]/text()')
        product_brand = extract_with_xpath(
            '//table[@class="productSpecification_table"]/tbody/tr/td[contains(text(),"Nhà sản xuất")]/../td[@class="value"]/text()')
        product_shop = 'Nguyễn Kim'
        product_rates = extract_with_xpath(
            '//div[@id="average_rating_product"]/span[@class="number_avg_rate_npv"]/text()')
        product_location = 'Hồ Chí Minh'
        product_sku = None
        product_instock = 1
        outofstock = extract_with_xpath(
            '//div[@id="out-of-stock"]/@style')
        if outofstock is not None and outofstock not in 'display: none':
            product_instock = 0

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
        products['rates'] = product_rates
        products['location'] = product_location
        products["domain"] = 'nguyenkim.com'
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
