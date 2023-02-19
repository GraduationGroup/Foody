from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from time import sleep
from threading import Thread, Barrier

import random
import math
import numpy as np


TIME_OUT_LIMIT = 20
MIN_DELAY = 0.5
MAX_DELAY = 1.5

NUMBER_OF_THREADS = 3


def randomDelay():
    delay_time = random.uniform(MIN_DELAY, MAX_DELAY)
    sleep(delay_time)


class FoodySpider:
    def __init__(self, numberOfThreads):
        self.FB_EMAIL = ""
        self.FB_PASSWORD = ""

        # URLS
        self.HOMEPAGE_URL = "https://www.foody.vn/"

        # set options and run driver

        options = webdriver.EdgeOptions()
        # options.add_argument("--headless")
        options.add_experimental_option("detach", True)

        self.driver = webdriver.Edge(executable_path="/msedgedriver.exe", options= options)
        self.driver.get(self.HOMEPAGE_URL)
        self.numberOfThreads = numberOfThreads

        # # login
        # self.fb_login(self.FB_EMAIL, self.FB_PASSWORD)

        # crawl by place
        self.traverse_provinces()


    def fb_login(self, driver, email, password):
        # driver.get(self.LOGIN_URL % returnUrl)
        
        randomDelay()

        driver.find_element(By.CSS_SELECTOR, "fieldset .social-accountkit-btn-phone").click()

        main_window_handle = driver.current_window_handle
        signin_window_handle = None

        while not signin_window_handle:
            for window_handle in driver.window_handles:
                if window_handle!= main_window_handle:
                    signin_window_handle = window_handle

        randomDelay()
        driver.switch_to.window(signin_window_handle)

        try:
            loginForm = WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.login_form_container')))

            randomDelay()
            loginForm.find_element(By.ID, "email").send_keys(email)
            randomDelay()
            loginForm.find_element(By.ID, "pass").send_keys(password)
            randomDelay()
            loginForm.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

            driver.switch_to.window(main_window_handle)

        except  TimeoutException:
            print("TIMEOUT")
            driver.quit()


    def traverse_provinces(self):
        randomDelay()
        # self.driver.get("https://www.foody.vn/")

        self.provinceHrefs = []
        try:
            head_province = WebDriverWait(self.driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#head-province .rn-nav-name')))

            # show popup
            head_province.click()
            popupLocation = self.driver.find_element(By.ID, "popupLocation")

            # traverse

            ul = WebDriverWait(popupLocation, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul li ul li ul')))
            provinces = ul.find_elements(By.TAG_NAME, "li")[:10]

            for province in provinces:
                href = province.find_element(By.TAG_NAME, "a").get_attribute("href")
                self.provinceHrefs.append(href) 

            self.driver.quit()


            # parallel crawl
            nPartSplit = math.ceil(len(self.provinceHrefs) / self.numberOfThreads)

            splitProvinceHrefs = np.array_split(np.array(self.provinceHrefs), nPartSplit)

            for smallHrefArr in splitProvinceHrefs:
                n = len(smallHrefArr)
                smallHrefArr = list(smallHrefArr)

                limit = n if n < self.numberOfThreads else self.numberOfThreads

                barrier = Barrier(limit)
                threads = []

                for href in smallHrefArr:
                    # randomDelay()
                    # self.driver.get(href)
                    # self.traverse_categories()
                    t = Thread(target=self.crawlByProvince, args=(href,barrier,)) 
                    t.start()
                    threads.append(t)
            
                for t in threads:
                    t.join()


        except  TimeoutException:
            print("TIMEOUT")
            self.driver.quit()
    

    def crawlByProvince(self, provinceUrl, barrier):
        options = webdriver.EdgeOptions()
        options.add_experimental_option("detach", True)

        driver = webdriver.Edge(executable_path="/msedgedriver.exe", options= options)
        driver.get(provinceUrl)

        #login
        btnLogin = WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.fd-btn-login-new')))
        btnLogin.click()

        randomDelay()
        self.fb_login(driver, self.FB_EMAIL, self.FB_PASSWORD)

        randomDelay()
        self.traverse_categories(driver)

        barrier.wait()


    def traverse_categories(self, driver):
        randomDelay()
        # self.driver.get("https://www.foody.vn/")

        cateHrefs = []

        try:
            head_category = WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#head-navigation')))

            # show popup
            head_category.click()
            menu_box = WebDriverWait(head_category, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.menu-box')))

            food = menu_box.find_elements(By.CSS_SELECTOR, "li")[1]
            categories = food.find_elements(By.CSS_SELECTOR, "ul li")[:10]
            
            # traverse
            for category in categories:
                c = category.find_element(By.TAG_NAME, "a")
                #title = c.get_attribute("title")
                href = c.get_attribute("href")
                cateHrefs.append(href)

            for href in cateHrefs:
                randomDelay()

                driver.get(href)
                self.traverse_restaurants(driver)


        except  TimeoutException:
            print("TIME OUT")
            driver.quit()


    def traverse_restaurants(self, driver):
        randomDelay()
        # self.driver.get("https://www.foody.vn/")
        resUrls = []
        try:
            totalPage = 1
            while True:
                print("PAGE %s" % totalPage)

                randomDelay()
                try: 
                    moreBtn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="scrollLoadingPage"]/a')))
                    driver.execute_script("arguments[0].click();", moreBtn)
                
                except TimeoutException:    
                    break

                totalPage+=1

            restaurants = driver.find_elements(By.XPATH, '//*[@id="result-box"]/div[1]/div/div/*')

            for res in restaurants:
                href = res.find_element(By.TAG_NAME, "a").get_attribute("href")
                # avatar = r.find_element(By.TAG_NAME, "img").get_attribute("src")
                # point = r.find_element(By.CSS_SELECTOR, ".status").text
                # name = r.find_element(By.TAG_NAME, "h2").text
                resUrls.append(href)
                  

            for url in resUrls:
                randomDelay()
                print(url)

                driver.get(url)

                chained_res = url.find("thuong-hieu")
                if chained_res == -1:
                    self.crawl_restaurant(driver)
                else:
                    self.traverse_chained_restaurants(driver)

        except TimeoutException:
            print("TIMEOUT")
            driver.quit()


    def traverse_chained_restaurants(self, driver):
        restaurants = driver.find_elements(By.XPATH, '//*[@id="FoodyApp"]/div[3]/div[1]/div[2]/div/div[1]/ul/li')
        resHrefs = []
        for res in restaurants:
            href = res.find_element(By.CSS_SELECTOR, "h2 a").get_attribute("href")
            resHrefs.append(href)

        for href in resHrefs:
            randomDelay()

            driver.get(href)
            self.crawl_restaurant(driver)


    def crawl_restaurant(self, driver):
        main_info = WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.main-info-title')))

        restaurant_name = WebDriverWait(main_info, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text

        try:
            restaurant_point = float(WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[itemprop=ratingValue]'))).text)
        except TimeoutException:
            restaurant_point = None

        try:
            restaurant_address = WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.res-common-add'))).text
        except TimeoutException:
            restaurant_address = None

        print(restaurant_name, restaurant_point, restaurant_address)


if __name__ == "__main__":
    foody_spider = FoodySpider(NUMBER_OF_THREADS)



