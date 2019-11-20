# -*- coding: utf-8 -*-
import scrapy
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
#import w3lib.html


from ..items import ProductItem

logger = logging.getLogger(__name__)


class VnexpressSpider(CrawlSpider):
    name = 'vnexpress'
    allowed_domains = ['shop.vnexpress.net']
    start_urls = ['https://shop.vnexpress.net/dien-thoai']
    rules = (
        Rule(LinkExtractor(
            allow=(
                '/dien-thoai/',
                '/dien-thoai/[\\w-]+/[\\w-]+$'
            ),
            deny=(
                '/tin-tuc/',
                '/phu-kien/',
                '/retail/',
                '/ho-tro/',
                '/tra-gop/',
                '/khuyen-mai/',
                'https://shop.vnexpress.net/mua-sam-uu-dai',
                'https://shop.vnexpress.net/thuong-hieu-uy-tin',
                'https://shop.vnexpress.net/xu-huong-mua-sam',
                'https://shop.vnexpress.net/cau-hoi-thuong-gap.html',
                'tel:1900633376'
            ),
        ), callback='parse_vnexpress'),
    )
    handle_httpstatus_list = [301, 302]

    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'webcrawler.middlewares.vnexpress.VnExpressSpiderMiddleware': 543
        },
    }

    def __init__(self, limit_pages=None, *a, **kw):
        super(VnexpressSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse_vnexpress(self, response):
        logger.info('Scrape url: %s' % response.url)
        for product_link in response.xpath('//div[@class="item-pro"]/div[@class="box box-image"]/a/@href').getall():
            yield response.follow(product_link, callback=self.parse_product_detail)

        # Following next page to scrape
        next_page = response.xpath(
            '//ul[@class="pagination pagination-lg"]/li/a[not(contains(@class,"active"))]/@href').get()
        if next_page is not None:
            match = re.match(r".*/page/(\d+).html", next_page)
            if match is not None:
                next_page_number = int(match.groups()[0])
                if next_page_number <= self.limit_pages:
                    yield response.follow(next_page, callback=self.parse_vnexpress)
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
            '//span[@class="price-current price_sp_detail"]/text()')
        # logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return
        else:
            product_price = self.parse_money(product_price)

        product_title = extract_with_xpath(
            '//h1[@class="product-title"]/text()')
        product_desc = extract_with_xpath(
            'normalize-space(//meta[@name="description"]/@content)')
        product_swatchcolors = extract_xpath_all(
            '//div[@class="similar-products"]/span/@rel')
        product_images = extract_xpath_all(
            '//div[@id="images_pro"]/a/@href')

        internalmemory = None
        brand = None

        # product_specifications = response.xpath('//div[@id="information"]/div/table[@class="table"]/tbody/tr/td//text()').getall()
        # product_specifications = []
        # specs = extract_xpath_all(
        #     '//div[@class="box-body box-information"]/text()')
        # if len(specs) > 0:
        #     product_specifications = [sp.strip() for sp in specs]
        product_specifications = []
        names = extract_xpath_all(
            '//div[@class="box-body box-information"]/table[@class="table"]/tbody/tr/td[1]//text()')
        values = extract_xpath_all(
            '//div[@class="box-body box-information"]/table[@class="table"]/tbody/tr/td[2]/text()')
        if len(names) > 0 and len(values) > 0:
            names = [' '.join(sp.split()) for sp in names]
            names = [sp.strip() for sp in names if sp != '']
            values = [' '.join(sp.split()) for sp in values]
            values = [sp.strip() for sp in values if sp != '']
            for index in range(1, len(names)):
                try:
                    if values[index] is not None and values[index] != '':
                        if 'ROM' in names[index]:
                            internalmemory = str(values[index])
                        if 'Thương hiệu' in names[index]:
                            brand = str(values[index])
                        spec_name = str(names[index]).replace(':', '').strip()
                        spec_value = str(values[index]).strip()
                        product_specifications.append(
                            [spec_name, spec_value])
                except IndexError as ie:
                    logger.error('IndexError: %s' % ie)
                except Exception as ex:
                    logger.error('Errors: %s' % ex)

        product_oldprice = 0
        oldprice = extract_with_xpath(
            '//span[@class="price-old price_old_sp_detail"]/text()')
        if oldprice is not None and oldprice != '':
            product_oldprice = self.parse_money(oldprice)
        else:
            product_oldprice = 0

        # product_internalmemory = extract_with_xpath(
        #     '//div[@class="box-body box-information"]/table[@class="table"]/tbody/tr/td[1]/label[contains(text(),"ROM")]/../td[2]/text()')
        product_internalmemory = internalmemory
        # product_brand = extract_with_xpath(
        #     '//div[@class="box-body box-information"]/table[@class="table"]/tbody/tr/td[1]/label[contains(text(),"Thương hiệu")]/../td/text()')
        product_brand = brand
        product_shop = extract_with_xpath(
            '//div[@class="info-supplier"]/div[@class="box-name"]/p/a/text()')
        product_rates = 0
        product_location = extract_with_xpath(
            '//div[@class="box-info-supplier"]/div[@class="info-address"]/p[@class="info-value"]/text()')
        product_sku = None
        product_instock = 1
        instock = extract_with_xpath(
            '//button[contains(@class,"add_to_cart_disable")]/text()')
        if instock is not None:
            if 'Hết hàng' in instock:
                product_instock = 0  # Out of stock

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
        products["domain"] = 'shop.vnexpress.net'
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
