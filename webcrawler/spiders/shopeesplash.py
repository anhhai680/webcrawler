# -*- coding: utf-8 -*-
import scrapy
import re
import logging
from scrapy_splash import SplashRequest

from ..items import ProductItem

logger = logging.getLogger(__name__)


script = """
function main(splash)
    splash:init_cookies(splash.args.cookies)
    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(0.5))
    return {
        cookies = splash:get_cookies(),
        html = splash:html()
    }
end
"""

script2 = """
function main(splash)
    splash:init_cookies(splash.args.cookies)
    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(0.5))
    return {
        cookies = splash:get_cookies(),
        html = splash:html()
    }
end
"""

script3 = """
function main(splash, args)
  splash.resource_timeout = 10.0
  splash.images_enabled = false
  splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36')
  assert(splash:go(splash.args.url))
  splash:wait(0.5)
  local scroll_to = splash:jsfunc("window.scrollTo")
  scroll_to(0, 'document.body.scrollHeight')
  splash:wait(0.5)
  local result, error = splash:wait_for_resume([[
    function main(splash) {
      var checkExist = setInterval(function() {
        if (document.querySelector('link[rel="next"]')) {
          clearInterval(checkExist);
          splash.resume('link[rel="next"] found');
        }
      }, 300);
    }
    ]],10)
  return {
    html=splash:html()
  }
end
"""

script4 = """
function main(splash, args)
  splash.resource_timeout = 10.0
  splash.images_enabled = false
  splash:set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36')
  splash:go(splash.args.url)
  splash:wait(0.5)
  local scroll_to = splash:jsfunc("window.scrollTo")
  scroll_to(0, 'document.body.scrollHeight')
  splash:wait(0.5)
  return {
    html=splash:html()
  }
end
"""


class ShopeesplashSpider(scrapy.Spider):
    name = 'shopee'
    allowed_domains = ['shopee.vn']
    start_urls = [
        'https://shopee.vn/Smartphone-%C4%90i%E1%BB%87n-tho%E1%BA%A1i-th%C3%B4ng-minh-cat.84.1979.19042']

    custom_settings = {
        'SPLASH_URL': 'http://0.0.0.0:8050',
        'SPLASH_COOKIES_DEBUG': False,
        'DOWNLOAD_DELAY': 1,
        'HTTPCACHE_STORAGE': 'scrapy_splash.SplashAwareFSCacheStorage',
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100
        },
        'USER_AGENT': {
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:35.0) Gecko/20100101 Firefox/35.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X x.y; rv:42.0) Gecko/20100101 Firefox/42.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.106 Safari/537.36 OPR/38.0.2220.41',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/600.7.12 (KHTML, like Gecko) Version/8.0.7 Safari/600.7.12',
            'Googlebot/2.1 (+http://www.google.com/bot.html)',
            'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/_BuildID_) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0)',
            'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/603.1.23 (KHTML, like Gecko) Version/10.0 Mobile/14E5239e Safari/602.1',
        }
    }

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, endpoint='execute', args={'lua_source': script3})

    def parse(self, response):
        logger.info('Scrape Url: %s', response.url)

        # Get product URL in page and yield Request
        links = response.xpath(
            '//div[@class="row shopee-search-item-result__items"]/div[@class="col-xs-2-4 shopee-search-item-result__item"]/div/a/@href').getall()
        logger.info('There is a total of ' + str(len(links)) + ' links')
        for product_link in links:
            try:
                product_link = "https://shopee.vn%s" % product_link
                yield SplashRequest(product_link,  callback=self.parse_product_detail, args={'wait': 3.0})
            except:
                pass

        # Get the next page and yield Request
        next_page = response.xpath('//link[@rel="next"]/@href').get()
        logger.info('Next page: %s', next_page)
        if next_page is not None:
            yield SplashRequest(next_page, self.parse, endpoint='execute', args={'lua_source': script3})
        else:
            logger.info('Next Page was not find on page %s', response.url)

    def parse_product_detail(self, response):

        def extract_with_xpath(query):
            return response.xpath(query).get(default='').strip()

        def extract_xpath_all(query):
            gallery = response.xpath(query).getall()
            return gallery

        def extract_price(query):
            price = response.xpath(query).get(default='').strip()
            if price is not None:
                price = price.split('-')[0]
            return price

        # Validate price with pattern
        price_pattern = re.compile(r'(\S*[0-9](\w+?))')
        product_price = extract_price(
            '//div[contains(@class,"items-center")]/div[@class="_3n5NQx"]/text()')
        # logger.info('Product Price: %s' % product_price)
        if re.match(price_pattern, product_price) is None:
            return

        product_title = extract_with_xpath('//div[@class="qaNIZv"]/text()')
        # product_desc = extract_with_xpath(
        #     '//div[@class="_2aZyWI"]/div[@class="_2u0jt9"]/span/text()')
        product_desc = response.css(
            'meta[name="description"]::attr("content")').get()
        product_swatchcolors = extract_xpath_all(
            '//div[@class="flex items-center crl7WW"]/button/text()')
        product_images = response.xpath(
            '//div[@class="_2MDwq_"]/div[@class="ZPN9uD"]/div[@class="_3ZDC1p"]/div/@style').re(r'(?:https?://).*?[^\)]+')

        # product_specifications
        product_specifications = []
        #backlist = ['Danh Mục', 'Kho hàng', 'Gửi từ', 'Shopee']
        for item in response.xpath('//div[@class="_2aZyWI"]/div[@class="kIo6pj"]'):
            try:
                key = item.xpath('.//label/text()').get().strip()
                value = item.xpath('.//a/text() | .//div/text()').get().strip()
                # if (key == '' or value == '') or key in backlist:
                #     break
                product_specifications.append({key, value})
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
        products['shop'] = 'shopee'
        products['domain'] = 'shopee.vn'
        products['body'] = ''

        yield products
