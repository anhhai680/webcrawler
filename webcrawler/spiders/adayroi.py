# -*- coding: utf-8 -*-
import scrapy
import logging
import json
import re
from scrapy.selector import Selector

from ..items import ProductItem

logger = logging.getLogger(__name__)


class AdayroiSpider(scrapy.Spider):
    name = 'adayroi'
    allowed_domains = ['adayroi.com']
    start_urls = [
        'https://rest.adayroi.com/cxapi/v2/adayroi/search?q=&categoryCode=323&pageSize=32']

    def __init__(self, limit_pages=None, *a, **kw):
        super(AdayroiSpider, self).__init__(*a, **kw)
        if limit_pages is not None:
            self.limit_pages = int(limit_pages)
        else:
            self.limit_pages = 300

    def parse(self, response):
        logger.info('Scrape url: %s' % response.url)
        try:
            sel = Selector(response=response, type="xml")
            if sel is not None:
                categoryCode = sel.xpath(
                    '//productSearchPage/categoryCode/text()').get()
                logger.info('categoryCode: %s' % categoryCode)

                for item in sel.xpath('//productSearchPage/products'):
                    # product_code = item.xpath('.//baseProductCode/text()').get()
                    product_code = item.xpath('.//code/text()').get()
                    logger.info('ProductCode: %s' % product_code)
                    if product_code is not None:
                        # product_link = 'https://rest.adayroi.com/cxapi/v2/adayroi/product/detail?fields=FULL&productCode=%s' % product_code
                        product_link = 'https://rest.adayroi.com/cxapi/v2/adayroi/product/detail?fields=FULL&offerCode=%s&search=' % product_code
                        logger.info('Product detail link: %s' % product_link)
                        yield response.follow(product_link, callback=self.parse_product_detail)

                # Next page: https://rest.adayroi.com/cxapi/v2/adayroi/search?q=&categoryCode=323&pageSize=32&page=2&currentPage=1
                page_number = 1
                current_page = 0
                total_pages = 0
                currentpage = sel.xpath(
                    '//productSearchPage/pagination/currentPage/text()').get()
                if currentpage is not None:
                    current_page = int(currentpage)
                totalpages = sel.xpath(
                    '//productSearchPage/pagination/totalPages/text()').get()
                if totalpages is not None:
                    total_pages = int(totalpages)

                if total_pages > 0:
                    while page_number <= total_pages:
                        if current_page > self.limit_pages:
                            break
                        try:
                            page_number += 1
                            next_page = 'https://rest.adayroi.com/cxapi/v2/adayroi/search?q=&categoryCode=323&pageSize=32&page={0}&currentPage={1}'.format(
                                page_number, current_page)
                            yield response.follow(next_page, callback=self.parse)
                        except Exception as ex:
                            logger.error(
                                'Could not follow to next page %s' % page_number)
                            break

        except Exception as ex:
            logger.error('Parse Errors: %s' % ex)
        pass

    def parse_product_detail(self, response):

        try:
            item = Selector(response=response, type="xml")
            if item is not None:
                product_title = item.xpath('//product/name/text()').get()
                product_desc = item.xpath(
                    '//product/description/text()').get().strip()

                oldprice = item.xpath(
                    '//product/productPrice/value/text()').get()
                product_oldprice = 0
                if oldprice is not None:
                    product_oldprice = self.parse_money(oldprice)

                price = item.xpath('//product/price/value/text()').get()
                product_price = 0
                if price is not None:
                    product_price = self.parse_money(price)

                product_swatchcolors = []
                for color in item.xpath('//product/productVariants/variantGroup'):
                    color_name = color.xpath('.//variantName/text()').get()
                    color_price = color.xpath('.//priceValue/text()').get()
                    color_price = self.parse_money(color_price)
                    color_url = 'https://adayroi.com%s' + \
                        color.xpath('.//productUrl/text()').get()

                    instock = 1  # In stock
                    productcode = color.xpath('.//productCode/text()').get()
                    if productcode is not None:
                        for code in item.xpath('//baseOptions/options'):
                            pcode = code.xpath('.//code/text()').get()
                            if pcode is not None and pcode == productcode:
                                stock = code.xpath(
                                    './/stock/stockLevelStatus/text()').get()
                                if stock is not None and stock != 'inStock':
                                    instock = 0

                    swatchcolors = {'name': color_name, 'value': {
                        'price': price,
                        'stock': instock,
                        'url': color_url
                    }}
                    product_swatchcolors.append(swatchcolors)

                product_internalmemory = None
                product_specifications = []
                for spec in item.xpath('//product/classifications/features'):
                    name = spec.xpath('.//name/text()').get()
                    value = spec.xpath('.//featureValues/value/text()').get()
                    if 'Bộ nhớ trong' in name:
                        product_internalmemory = value + 'GB'
                    product_specifications.append([name, value])

                # product images
                product_images = []
                jsonMedias = item.xpath(
                    '//product/jsonMedias/text()').get()
                if jsonMedias is not None:
                    images = json.loads(jsonMedias)
                    if len(images) > 0:
                        for json_img in images:
                            img_url = json_img['zoomUrl']
                            product_images.append(img_url)

                plink = item.xpath('//product/url/text()').get()
                product_link = 'https://adayroi.com%s' % plink

                product_brand = item.xpath('//product/brandName/text()').get()
                product_shop = item.xpath(
                    '//product/merchant/merchantName/text()').get()
                product_rates = 0
                product_location = 'Hồ Chí Minh'
                product_sku = item.xpath('//product/sapSku/text()').get()
                product_instock = 1
                instock = item.xpath(
                    '//product/stock/stockLevelStatus/text()').get()
                if instock is not None:
                    if instock != 'inStock':
                        product_instock = 0  # Out of stock

                products = ProductItem()
                products['cid'] = 'dienthoai'  # 1: Smartphone
                products['title'] = product_title
                products['description'] = product_desc
                products['oldprice'] = product_oldprice
                products['price'] = product_price
                products['swatchcolors'] = product_swatchcolors
                products['internalmemory'] = product_internalmemory
                products['specifications'] = product_specifications
                products['link'] = product_link
                products['images'] = product_images
                products['brand'] = product_brand
                products['shop'] = product_shop
                products['rates'] = product_rates
                products['location'] = product_location
                products['domain'] = 'adayroi.com'
                products['sku'] = product_sku
                products['instock'] = product_instock
                products['body'] = ''

                yield products

        except Exception as ex:
            logger.error('Parse product_detail Errors: %s' % ex)
        pass

    def parse_money(self, value):
        if str(value).isdigit():
            return value
        return re.sub(r'[^\d]', '', str(value))
