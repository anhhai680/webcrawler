# webcrawler
# These are commands to run multiple spiders at time by scrapyd on local
curl http://localhost:6800/schedule.json -d project=webcrawler -d spider=adayroi
curl http://localhost:6800/schedule.json -d project=webcrawler -d spider=cellphones
curl http://localhost:6800/schedule.json -d project=webcrawler -d spider=fptshop
# This command to cancel currently or specific job is running
curl http://localhost:6800/cancel.json -d project=webcrawler -d job=6487ec79947edab326d6db28a2d86511e8247444

# Shopee
# To get all products by category id
https://shopee.vn/api/v2/search_items/?by=relevancy&keyword=Smartphone%20-%20%C4%90i%E1%BB%87n%20tho%E1%BA%A1i%20th%C3%B4ng%20minh&limit=50&match_id=19042&newest=0&order=desc&page_type=search
# To get product detail by item id and shop id
https://shopee.vn/api/v2/item/get?itemid=2183317956&shopid=54057688
# To display images on website
https://cf.shopee.vn/file/27d55303ff8b4bb546837b1d756bd904
# Here's format to make a product detail's link
https://shopee.vn/i%E1%BB%87n%20tho%E1%BA%A1i%20smartphone%20XS%20mini-i.54057688.2183317956

# Mysql's query example to help testing only purpose:
- select * from ecrawdb.crawl_products as p inner join ecrawdb.crawl_blacklinks as b on p.link = b.link;
- alter table ecrawdb.crawl_products auto_increment=1;

# Test scrapy shell inside command line
url = 'http://www.example.com'
request = scrapy.Request(url, headers={'User-Agent': 'Mybot'})
fetch(request)

# Install MySQL Server on Ubuntu
sudo apt install mysql-server
sudo systemctl status mysql

# Google cache of site
https://webcache.googleusercontent.com/search?q=cache:lazada.vn/dien-thoai-di-dong/
