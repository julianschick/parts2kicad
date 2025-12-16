from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


def web():
    chrome_options = Options()
    #chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.mouser.de/ProductDetail/RECOM-Power/R-785.0-0.5?qs=YWgezujkI1KPMF6NhJFaJw%3D%3D")
    sleep(15)
    btn = driver.find_element(By.ID, "lnk_CadModel")
    print(btn)
