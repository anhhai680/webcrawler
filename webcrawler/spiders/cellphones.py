# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.spidermiddlewares.httperror import HttpError


from ..items import ProductItem

logger = logging.getLogger(__name__)


class CellphonesSpider(scrapy.Spider):
    name = 'cellphones'
    allowed_domains = ['cellphones.com.vn']
    start_urls = [
        'https://cellphones.com.vn/mobile.html',
        # 'https://cellphones.com.vn/tablet.html',
        # 'https://cellphones.com.vn/hang-cu.html',
    ]
    # rules = (
    #     Rule(LinkExtractor(
    #         allow=(
    #             'mobile.html',
    #             'mobile.html?p=[0-9]',
    #             # 'https://cellphones.com.vn/mobile/[\\w-]+/[\\w-]+$',
    #         ), deny=(
    #             'itel-it2123v.html',
    #             'dien-thoai-pho-thong.html',
    #             'timkiem.html',
    #             '/sforum/'
    #             'mobile.html#top',
    #         ), deny_domains=(
    #             'https://cellphones.com.vn/mobile.html?model_dienthoai_mtb=[0-9]',
    #             'https://cellphones.com.vn/mobile.html?screen_size=[0-9]',
    #             'https://cellphones.com.vn/mobile.html?storage=[0-9]',
    #             'https://cellphones.com.vn/mobile.html?sim_card=[0-9]',
    #             'https://cellphones.com.vn/mobile.html?operating_system=[0-9]'
    #         ),
    #     ), callback='parse_cellphones'),
    # )

    def __init__(self, limit_pages=None, *a, **kw):
        super(CellphonesSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape url: %s' % response.url)
        # Get all product links on current page
        for link_product in response.css('div.lt-product-group-image>a::attr(href)'):
            if link_product is not None:
                yield response.follow(link_product, self.parse_product_detail)

        # Following to scrape for next page
        next_page = response.xpath(
            '//link[@rel="next"]/@href').get()
        if next_page is not None:
            match = re.match(r".*?p=(\d+)", next_page)
            if match is not None:
                next_page_number = int(match.groups()[0])
                if next_page_number <= self.limit_pages:
                    yield response.follow(next_page, callback=self.parse)
                else:
                    logger.info('Spider will be stop here.{0} of {1}'.format(
                        next_page_number, next_page))
        # num_page = response.xpath(
        #     '//div[@class="pages"]/ul[@class="pagination"]/li[not(contains(@class,"active"))]/a/text()').re(r'\d+')[-1]
        # total_of_page = int(num_page)
        # if total_of_page > 0:
        #     next_page = 1
        #     while (next_page <= total_of_page):
        #         next_page += 1
        #         next_link = 'https://cellphones.com.vn/mobile.html?p=%s' % next_page
        #         yield response.follow(next_link, callback=self.parse_cellphones)
        pass

    # Following product detail to scrape all information of each product
    def parse_product_detail(self, response):

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
        else:
            product_price = self.parse_money(product_price)

        product_title = extract_with_xpath('//h1/text()')
        product_desc = extract_with_xpath(
            '//meta[@name="description"]/@content')
        product_swatchcolors = extract_xpath_all(
            '//label[@class="opt-label"]/span[@class="opt-name"]/text()')
        # product_swatchcolors = extract_with_xpath(
        #     '//ul[@id="configurable_swatch_color"]/li[contains(@class,"selected")]/a/@title')

        # product_images = response.xpath(
        #     '//div[@id="product-more-images"]/div[@class="lt-product-more-image"]/a/@onclick').re(r'(https\S+)\'')
        product_images = extract_xpath_all(
            '//div[@class="product-image"]/div[@class="product-image-gallery"]/img/@src | //div[@class="product-img-box left"]/img/@src')
        if len(product_images) <= 0:
            product_images = response.xpath(
                '//div[@id="product-more-images"]/div[@class="lt-product-more-image"]/a/@onclick').re(r'(https\S+)\'')
        #logger.info('Gallery: {} of product link: {}'.format(product_images, product_link))

        # Specifications product
        # product_specifications = response.xpath(
        #     '//table[@id="tskt"]/tr/*/text()').re('(\\w+[^\n]+)')
        # product_specifications = []
        # for spec_row in response.xpath('//table[@id="tskt"]/tr'):
        #     if spec_row is not None:
        #         try:
        #             spec_key = spec_row.xpath('.//td/text()')[0].get().strip()
        #             spec_value = spec_row.xpath(
        #                 './/td/text()')[1].get().strip()
        #             product_specifications.append({spec_key, spec_value})
        #         except:
        #             pass
        product_specifications = []
        names = extract_xpath_all('//table[@id="tskt"]//td[1]/text()')
        values = extract_xpath_all('//table[@id="tskt"]//td[2]/text()')
        for index in range(len(names)):
            if values[index] is not None and values[index] != '':
                spec_name = str(names[index]).strip()
                spec_value = str(values[index]).strip()
                product_specifications.append([spec_name, spec_value])

        product_oldprice = 0
        oldprice = extract_with_xpath(
            '//p[@class="old-price"]/span[@id="old-price-12388"]/text()')
        if oldprice is not None and oldprice != '':
            product_oldprice = self.parse_money(oldprice)
        else:
            product_oldprice = 0

        # product_internalmemory = extract_with_xpath(
        #     '//div[@class="linked"]/a[contains(@class,"active")]/span/text()')
        # if product_internalmemory is None or product_internalmemory == '':
        product_internalmemory = extract_with_xpath(
            '//table[@id="tskt"]//td[contains(text(),"Bộ nhớ trong")]/../td[2]/text()')

        product_brand = extract_with_xpath(
            '//tr[@itemprop="brand"]/td[@itemprop="name"]/text()')
        product_shop = 'Cellphones'
        product_rates = 0
        product_location = 'Hồ Chí Minh'
        product_sku = None
        product_instock = 1

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
        products['shop'] = product_shop
        products['rates'] = float(product_rates)
        products['location'] = product_location
        products['domain'] = 'cellphones.com.vn'
        products['sku'] = product_sku
        products['instock'] = product_instock
        products['body'] = ''  # response.text

        yield products

    def parse_money(self, value):
        try:
            if str(value).isdigit():
                return value
            return re.sub(r'[^\d]', '', str(value))
        except Exception as ex:
            logger.error('parse_money errors: %s' % ex)
