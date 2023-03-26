from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from time import sleep
from threading import Thread
from datetime import datetime

import pymongo
import random
import numpy as np

TIME_OUT_LIMIT = 600
NUMBER_OF_THREADS = 1


def randomDelay():
    delay_time = random.uniform(0.5, 1.5)
    sleep(delay_time)

class Database:
    def __init__(self):
        self.URI = "mongodb+srv://npvu1510:Phanvu2001@cluster0.cd4eojq.mongodb.net/?retryWrites=true&w=majority"
        try:
            self.client = pymongo.MongoClient(self.URI)  
            print("Setup DB completely !!!")
            
        except Exception:
            print("ERROR:", Exception)
            exit()
    
    def insertRes(self, resObj):
        return self.client['POI'].foody.insert_one(resObj)
    


class FoodySpider:
    def __init__(self, numberOfThreads):
        self.numberOfThreads = numberOfThreads

        # inits
        self.initIn4()
        self.initDriver()

        # mongodb
        self.db = Database()

        # crawl
        self.start_crawl()
        

    def initIn4(self):
        # urls
        self.LOGIN_URL = "https://id.foody.vn/account/login?returnUrl=https://www.foody.vn/"
        self.HOME_URL = "https://www.foody.vn/"

        # auth
        self.FB_EMAIL = "84927389235"
        self.FB_PASSWORD = "linhchim1302"
    

    def initDriver(self):
        # set options
        options = webdriver.EdgeOptions()
        options.add_argument("--headless")
        options.add_argument("user-agent=User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.54")
        options.add_experimental_option("detach", True)

        # init drivers and threads
        self.mainDriver = webdriver.Edge(executable_path="/msedgedriver.exe", options= options)
        self.drivers = []
        for i in range(self.numberOfThreads):
            driver = webdriver.Edge(executable_path="/msedgedriver.exe", options= options)
            self.drivers.append(driver)


    def start_crawl(self):
        self.mainDriver.get(self.HOME_URL)
        self.traverse_provinces()


    def traverse_provinces(self):
        randomDelay()
        # self.driver.get("https://www.foody.vn/")
        proHrefs = []
        try:
            # show popup
            head_province = WebDriverWait(self.mainDriver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#head-province .rn-nav-name')))
            head_province.click()
    
            popupLocation = self.mainDriver.find_element(By.ID, "popupLocation")

            # traverse
            ul = WebDriverWait(popupLocation, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul li ul li ul')))
            provinces = ul.find_elements(By.TAG_NAME, "li")

            for province in provinces:
                href = province.find_element(By.TAG_NAME, "a").get_attribute("href")
                proHrefs.append(href) 
            
            self.mainDriver.quit()

            # set up threads
            proHrefs = np.array_split(np.array(proHrefs), self.numberOfThreads)

            self.threads = []
            for i in range(self.numberOfThreads):
                t = Thread(target=self.crawlByProvince, args=(self.drivers[i], proHrefs[i], i,))
                t.start()
                self.threads.append(t)
                sleep(1)
            
            for t in self.threads:
                t.join()
                


        except  TimeoutException:
            
            self.mainDriver.quit()
    

    def fb_login(self, driver):
        driver.get(self.LOGIN_URL)

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
            loginForm.find_element(By.ID, "email").send_keys(self.FB_EMAIL)
            randomDelay()
            loginForm.find_element(By.ID, "pass").send_keys(self.FB_PASSWORD)
            randomDelay()
            loginForm.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

            driver.switch_to.window(main_window_handle)

            WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.CLASS_NAME, 'ico-search')))


        except  TimeoutException:
            
            driver.quit()


    def crawlByProvince(self, driver, proHrefs, id, barrier = None):
        #login
        self.fb_login(driver)

        print(f"THREAD {id}: Login!!!")
        for href in proHrefs:
            driver.get(href)
            self.traverse_categories(driver, id)


    def traverse_categories(self, driver, id):
        # self.driver.get("https://www.foody.vn/")
        catHrefs = []

        try:            
            # show popup
            head_category = WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#head-navigation')))
            head_category.click()

            sleep(2)
            menu_box = WebDriverWait(head_category, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.menu-box')))

            food = menu_box.find_elements(By.CSS_SELECTOR, "li")[1]
            categories = food.find_elements(By.CSS_SELECTOR, "ul li")[:10]
            
            # traverse
            for category in categories:
                c = category.find_element(By.TAG_NAME, "a")
                #title = c.get_attribute("title")
                href = c.get_attribute("href")
                catHrefs.append(href)
            
            for href in catHrefs:
                driver.get(href)
                self.traverse_restaurants(driver, id)

        except  TimeoutException:
            print("TIME OUT")
            driver.quit()


    def traverse_restaurants(self, driver, id):
        print(f"THREAD {id}: {driver.current_url}")
        randomDelay()
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
                if isinstance(href, str):
                    resUrls.append(href)
                  

            for url in resUrls:
                print(url)
                driver.get(url)

                chained_res = url.find("thuong-hieu")
                if chained_res == -1:
                    self.crawl_restaurant(driver)
                else:
                    self.traverse_chained_restaurants(driver)

        except TimeoutException:
            
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
        resName = WebDriverWait(main_info, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).text

        try:
            resRating = float(WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[itemprop=ratingValue]'))).text)
        except TimeoutException:
            resRating = None

        try:
            resAddr = WebDriverWait(driver, TIME_OUT_LIMIT).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.res-common-add'))).text
        except TimeoutException:
            resAddr = None

        self.db.insertRes({"name": resName, "rating": resRating, "address": resAddr, "url": driver.current_url, "createdAt": datetime.now()})


if __name__ == "__main__":
    FoodySpider(NUMBER_OF_THREADS)
