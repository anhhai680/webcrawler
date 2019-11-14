from scrapy.commands import ScrapyCommand
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import requests
import logging


class AllCrawlCommand(ScrapyCommand):
    requires_project = True
    default_settings = {'LOG_ENABLED': False}

    def short_desc(self):
        return "Schedule a run for all available spiders (run scrapy server first)"

    def run(self, args, opts):
        settings = get_project_settings()
        crawlers = CrawlerProcess(settings)
        url = 'http://localhost:6800/schedule.json'
        for spider_name in crawlers.spiders.list():
            values = {'project': 'webcrawler', 'spider': spider_name}
            req = requests.post(url, data=values)
            print("Running spider %s" % (spider_name))
        pass
