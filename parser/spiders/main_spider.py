import pandas as pd
import scrapy
from scrapy_selenium import SeleniumRequest
from selenium import webdriver
from selenium.webdriver.common.by import By


class CategorySpider(scrapy.Spider):
    name = 'main_spider'

    def start_requests(self):
        start_url = 'https://order-nn.ru/kmo/catalog/5999/?PAGEN_1=1' #, 'https://order-nn.ru/kmo/catalog/9460/?PAGEN_1=1' #'https://order-nn.ru/kmo/catalog/5974/?PAGEN_1=1' #, 'https://order-nn.ru/kmo/catalog/9460/?PAGEN_1=1',
                      #'https://order-nn.ru/kmo/catalog/5999/?PAGEN_1=1']
        #for url in start_urls:
        yield SeleniumRequest(url=start_url, callback=self.parse)

    def parse(self, response):
        pagination = response.xpath(
            '//div[@class="top-control-block_7"]/ul[@class="ul-pagination"]/li[position()=last()-1]/a/text()').get()

        for item in response.xpath('//div[@class="horizontal-product-item-block_3_2"]/a/@href'):
            yield response.follow(item, callback=self.parse_products)

        for page in range(2, int(pagination) + 1):
            next_page = f'{response.url.replace(f"?PAGEN_1={page - 1}", f"?PAGEN_1={page}")}'
            yield response.follow(next_page, callback=self.parse)

    def parse_products(self, response):
        price = response.xpath('//div[@class="block-3-row element-current-price"]/span[@itemprop="price"]/text()').get()

        options = webdriver.FirefoxOptions()
        options.binary_location = '/Applications/Firefox.app/Contents/MacOS/Firefox'
        options.add_argument('--headless')
        driver = webdriver.Firefox(
            options=options,
        )
        driver.get(url=response.url)

        table = driver.find_elements(By.XPATH, '//table[@class="table table-striped table-character"]//tr')

        data = []
        for t in table:
            data.append(t.text)

        row_data = {
            'name': response.xpath('//div[@class="block-1-0"]/h1[@itemprop="name"]/text()').get(),
            'price': ('Нет в наличии' if price is None else response.xpath(
                '//div[@class="block-3-row element-current-price"]/span[@itemprop="price"]/text()').get()),
            'description': response.xpath('//div[@id="for_parse"]/p/text()').get(),
            'characters': [data]
        }

        driver.close()
        driver.quit()

        df = pd.DataFrame(row_data, columns=['name', 'price', 'description', 'characters'])
        df.to_csv('/Users/faithk/Documents/parser/data.csv', mode='a', index=False, header=False)