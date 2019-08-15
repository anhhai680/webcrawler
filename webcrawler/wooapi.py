# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
from scrapy.exceptions import DropItem
from woocommerce import API


class WoocommercePipeline(object):

    def __init__(self):
        try:
            self.wcapi = API(
                url="https://vivumuahang.com/",
                consumer_key="ck_e7b56c6e85a00b80b41605548c63aeb5cfa54868",
                consumer_secret="cs_83582ad6bcd50f08daef5e0033f1760582bd184a",
                wp_api=True,  # Enable the WP REST API integration
                version="wc/v3",  # WooCommerce WP REST API version
                timeout=60
            )
        except Exception as ex:
            raise ex

    def addcategory(self, category_name, parent=None):
        """
        Check a category is existing or not. If it does not exist, call an api to create this category
        """

        try:
            data = {
                "name": category_name,
                "parent": parent
            }
            result = self.wcapi.post('products/categories', data).json()

            if len(result) <= 0:
                return None

            if 'id' in result:
                return result['id']
            else:
                code = result['code']
                if code == 'term_exists':
                    return result['data']['resource_id']
                else:
                    return None
        except:
            # self.logger.error(
            #     'New category {} was exception with {}'.format(category_name, ex))
            return None

    def addtags(self, tag_name):
        """
        Add a new product's tags
        """

        try:
            data = {
                "name": tag_name
            }
            result = self.wcapi.post('products/tags', data).json()

            if len(result) <= 0:
                return 0

            if 'id' in result:
                return result['id']
            else:
                code = result['code']
                if code == 'term_exists':
                    return result['data']['resource_id']
                else:
                    return 0
        except:
            return 0

    def process_item(self, item, spider):
        """
        Product type. Options: simple, grouped, external and variable. Default is simple.
        """

        try:
            parent_id = 15  # Smartphone

            title = item['title']
            price = parse_money(item["price"])
            short_description = item['description']
            images = [{'src': img} for img in item['images']]
            link = item['link']
            brand = item['brand']
            shop = item['shop']
            swatchcolors = ' - '.join(item['swatchcolors'])
            # specifications = [re.split(':', rd)
            #                   for rd in item["specifications"]]
            specifications = item["specifications"]

            # if item["specifications"] is not None:
            #     try:
            #         specifications = json.dumps(
            #             list(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
            #     except:
            #         specifications = json.dumps(
            #             dict(item["specifications"]), separators=(',', ':'), ensure_ascii=False)
            #         pass

            #spider.logger.info('Technical specifications: %s' % specifications)
            catid = self.addcategory(brand, parent_id)
            if not isinstance(catid, int):
                spider.logger.info('Category Id result is %s' % str(catid))
                return None

            tag_brand_id = self.addtags(brand)
            #tag_shop_id = self.addtags(shop)
            body_content = ' \n '.join(specifications)
            rates = str(item['rates'])
            domain = item['domain']

            data = {
                "name": title,
                "type": "external",
                "regular_price": price,
                "description": body_content,
                "short_description": short_description,
                "categories": [
                    {
                        "id": parent_id  # Smartphone
                    },
                    {
                        "id": catid
                    }
                ],
                "images": images,
                "external_url": link,
                "button_text": "Đến nơi bán",
                # "attributes": [
                #     {
                #         "id": 2,  # Color
                #         "visible": True,
                #         "options": swatchcolors
                #     }
                # ],
                "tags": [
                    {"id": tag_brand_id},
                ],
                "meta_data": [
                    {'key': 'brand', 'value': brand},
                    {'key': 'shop', 'value': shop},
                    {'key': 'rates', 'value': rates},
                    {'key': 'external_url', 'value': link},
                    {'key': 'domain', 'value': domain},
                    {'key': 'swatch', 'value': swatchcolors}
                ]
            }

            spider.logger.info('Product data: %s' % data)

            try:
                result = self.wcapi.post("products", data).json()
                if len(result) <= 0:
                    spider.logger.info(
                        'Woocommerce API has been errors %s' % result)
                    return None

                if 'id' in result:
                    spider.logger.info(
                        'Successfull added a new product with Id: %s' % result['id'])
                else:
                    spider.logger.error(
                        'Insert product failed with errors: %s' % result)
            except ValueError as ex:
                raise DropItem(
                    'Create new product failed with errors: {}'.format(ex))

            return item

        except Exception as ex:
            raise DropItem(
                'Product {} inserted failure with errors {}'.format(item, ex))

        return None


def parse_money(value):
    if str(value).isdigit():
        return value
    return re.sub(r'[^\d]', '', str(value))
