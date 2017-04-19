#!/usr/bin/env python3

#author: Steven Miller

from selenium import webdriver
import requests
import base64
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, ElementNotVisibleException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui
#from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from random import randint

def write_xpath(driver, xpath,write):
    elem = driver.find_element_by_xpath(xpath)
    elem.send_keys(write)

def write_by_name(driver, name,write):
    elem = driver.find_element_by_name(name)
    elem.send_keys(write)

def click_id(driver, id_is):
    div = driver.find_element_by_id(id_is)
    div.click()

def frame_switch(driver, css_selector):
    driver.switch_to.frame(driver.find_element_by_css_selector(css_selector))

def get_phantom_driver():
    username = 'TODO'+str(randint(1000,10000000))
    password = "TODO"
    service_args = [
                '--proxy=http://TODO:TODO',
                '--proxy-type=http',
                '--proxy-auth='+username+":"+password
                   ]
    driver = webdriver.PhantomJS('./phantomjs-2.1.1-linux-x86_64/bin/phantomjs',service_args=service_args)

    headers = { 'Accept':'*/*',
        'Accept-Encoding':'gzip, deflate, sdch',
        'Accept-Language':'en-US,en;q=0.8',
        'Cache-Control':'max-age=0',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36'
    }

    for key, value in enumerate(headers):
        webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.customHeaders.{}'.format(key)] = value
    return driver

def get_new_driver():
    #options = webdriver.ChromeOptions()
    #options.add_argument("--start-maximized")
    #driver = webdriver.Chrome(chrome_options=options)
    #driver.set_window_size(1920,1080)
    #driver.maximize_window()
    '''
    driver = webdriver.Firefox()
    driver.maximize_window()
    '''
    driver = webdriver.PhantomJS()
    return driver

def requests_session_now(driver):
    agent = driver.execute_script("return navigator.userAgent")
    headers = {
    "User-Agent": agent
    }
    session = requests.Session()
    session.headers.update(headers)
    for cookie in driver.get_cookies():
        c = {cookie['name']: cookie['value']}
        session.cookies.update(c)
    return session

def is_css_present(driver,css,recursion_depth=0):
    if recursion_depth > 5:
        print("ERROR: recursed past max depth of 5 trying to check if a css was present: "+css)
        quit()
    try:
        elems = driver.find_elements_by_css_selector(css)
        return (len(elems) > 0)
    except UnexpectedAlertPresentException:
        find_accept_alert(driver)
        return is_css_present(driver,css,recursion_depth+1)
