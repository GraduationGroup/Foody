from selenium import webdriver
from selenium.webdriver.common.by import By

class ShopeeFoodSpider:
    def __init__(self):        
        # URLS
        self.HOMEPAGE_URL = "https://shopeefood.vn/"

        options = webdriver.EdgeOptions()
        # options.add_argument("--headless")
        options.add_experimental_option("detach", True)

        self.driver = webdriver.Edge(executable_path="/msedgedriver.exe", options= options)
        self.driver.get(self.HOMEPAGE_URL)


if __name__ == "__main__":
    shopee_Spider = ShopeeFoodSpider()


