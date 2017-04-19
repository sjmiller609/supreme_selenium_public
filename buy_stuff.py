#!/usr/bin/env python3
import requests
import re
import lxml.html
from lxml import etree
from random import randint
import json
import datetime
from datetime import datetime as dt, tzinfo
from random import randint
from subprocess import check_output, CalledProcessError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from time import sleep
import string
import zipfile

def create_proxyauth_extension(proxy_host, proxy_port,
                               proxy_username, proxy_password,
                               scheme='http', plugin_path=None):
    """Proxy Auth Extension

    args:
        proxy_host (str): domain or ip address, ie proxy.domain.com
        proxy_port (int): port
        proxy_username (str): auth username
        proxy_password (str): auth password
    kwargs:
        scheme (str): proxy scheme, default http
        plugin_path (str): absolute path of the extension       

    return str -> plugin_path
    """
    print(timestamp()+" creating plug in")

    if plugin_path is None:
        plugin_path = '/tmp/vimm_chrome_proxyauth_plugin.zip'

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
    """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "${scheme}",
                host: "${host}",
                port: parseInt(${port})
              },
              bypassList: ["foobar.com"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "${username}",
                password: "${password}"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )
    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    print(timestamp()+" created plug in")

    return plugin_path


def pretty_print(jsonin):
    print(json.dumps(jsonin,indent=4,separators=(',',': ')))

def get_local_instance_id():
    response = requests.get("http://169.254.169.254/latest/meta-data/instance-id")
    if "200" not in str(response):
        print("ERROR: querying local instance id")
        print(response)
        print(response.text)
        quit()
    re_id = re.compile("i-[a-z0-9]*")
    if not re_id.match(response.text):
        print("ERROR: did not get an id when querying for ours.")
        print(response)
        print(response.text)
        quit()
    return response.text

def stop_container():
    print(timestamp()+"killing docker container(s)")
    command = "docker ps -q"
    containers = check_output(command.split()).split(b"\n")
    command = "docker kill "
    for x in containers:
        if len(x) > 0:
            command += x.decode("utf-8")+" "
    check_output(command.split())

def start_container():
    print(timestamp()+" starting container...")
    command = 'docker run -d -p 127.0.0.1:4444:4444 -p 5900:5900 selenium/standalone-chrome-debug:3.0.1-germanium'
    try:
        check_output(command.split())
    except CalledProcessError:
        return
        print(timestamp()+"detected a container is up")
        stop_container()
        check_output(command.split())
    response = ""
    timeleft = 30
    print(timestamp()+" waiting for it to be ready...")
    while "200" not in str(response) and timeleft > 0:
        sleep(1)
        timeleft -= 1
        try:
            response = requests.get("http://127.0.0.1:4444/wd/hub")
        except:
            pass
    print(timestamp()+" it's ready.")

def timestamp():
    return str(datetime.datetime.today())+" "

def get_driver():
    start_container()
    seed = randint(10000,1000000000)
    proxyauth_plugin_path = create_proxyauth_extension(
        proxy_host="TODO",
        proxy_port=0,#TODO
        proxy_username="TODO"+str(seed),
        proxy_password="TODO"
    )
    co = webdriver.ChromeOptions()
    user_agent = 'Mozilla/5.0 (Linux; <Android Version>; <Build Tag etc.>) AppleWebKit/<WebKit Rev> (KHTML, like Gecko) Chrome/<Chrome Rev> Mobile Safari/<WebKit Rev>'
    co.add_argument("user-agent="+user_agent)
    co.add_argument("--start-maximized")
    print(timestamp()+"adding extention to chrome options")
    co.add_extension(proxyauth_plugin_path)
    print(timestamp()+"connecting to remote driver.")
    driver = None
    for _ in range(0,60):
        sleep(1)
        try:
            driver = webdriver.Remote(
                command_executor='http://127.0.0.1:4444/wd/hub',
                desired_capabilities=co.to_capabilities())
        except:
            pass
        if driver is not None:break
    return driver

def get_num_twins(tree):
    if len(tree) == 0: return [0,""]
    first_tag = tree[0].tag
    count = 0
    for child in tree:
        if child.tag == first_tag:
            count += 1
        else:
            return [-1,""]
    return [count,first_tag]

#this is an algorithm that could be an interview quesiton or something
# there is likely room for improvment
def find_tag_with_most_and_only_twins(tree):
    final_result = get_num_twins(tree)
    num_twins_children = []
    for i in range(0,len(tree)):
        num_twins_children.append(find_tag_with_most_and_only_twins(tree[i]))
    for result in num_twins_children:
        if result[0] > final_result[0]:
            final_result = result
    return final_result
        

def get_article_tag_name(html):
    #html is a tree here.
    max_count = 0
    tag_name = find_tag_with_most_and_only_twins(html)[1]
    return tag_name

def get_matching_xpaths(root,current,xpaths,keywords,tag_name):
    if current.tag == tag_name:
        content = str(lxml.html.tostring(current).lower())
        if "sold out" not in content:
            matched = 0
            for keyword in keywords:
                if keyword.strip().lower() in content:
                    matched += 1
            if matched == len(keywords):
                xpaths.append(root.getpath(current))
    else:
        for child in current:
            get_matching_xpaths(root,child,xpaths,keywords,tag_name)

def match_keywords_and_not_sold_out(html_source,keywords):
    tree = lxml.html.fromstring(html_source)
    tag_name = get_article_tag_name(tree)
    xpaths = []
    eroot = etree.ElementTree(tree)
    get_matching_xpaths(eroot,tree,xpaths,keywords,tag_name)
    return xpaths

#very ineffcient time-wise, but most durable i think.
#many redudant searches
#we look down any path that contains add to cart, 
# and we return the deepest xpath
def find_cart_xpath(eroot,tree,text,depth=0):
    if text not in str(lxml.html.tostring(tree).lower()):
        return [None,-1]
    result = [None,depth]
    found_child = False
    for child in tree:
        child_xpath = find_cart_xpath(eroot,child,text,depth=depth+1)
        if child_xpath[1] > result[1]:
            result = child_xpath
            found_child = True
    if not found_child:
        xpath_max = eroot.getpath(tree)
        result[0] = xpath_max
    return result

#durability heavily prioritized over speed
def find_deepest_xpath_containing(driver,text):
    tree = lxml.html.fromstring(driver.page_source)
    eroot = etree.ElementTree(tree)
    cart_xpath = find_cart_xpath(eroot,tree,text)[0]
    return cart_xpath

def find_all_xpath_containing(driver,text):
    tree = lxml.html.fromstring(driver.page_source)
    eroot = etree.ElementTree(tree)
    cart_xpath = find_cart_xpath(eroot,tree,text)[0]
    return cart_xpath

def send_keys(driver,keys):
    ActionChains(driver).send_keys(keys).perform()

def press_tab(driver):
    ActionChains(driver).send_keys(Keys.TAB).perform()
    
def press_shift_tab(driver):
    ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.TAB).key_up(Keys.SHIFT).perform()

print("------------- BEGIN PYTHON -------------")
id_ = get_local_instance_id()
print("my id is "+id_)
print(timestamp()+"getting info from server")
#for the server code, see the other repository 'billing_server_public'.
response = requests.get("http://TODO:TODO/billing/"+id_)
print(timestamp()+"got it:")
print(response)
json_input = json.loads(response.text)
pretty_print(json_input)
driver = get_driver()
print(timestamp()+"getting google")
driver.get("http://google.com")
print(timestamp()+driver.current_url)
print(response)
print(timestamp()+"getting drop link")
driver.get(json_input["drop_link"])
if json_input["drop_link"] in driver.current_url:
    print(timestamp()+"successfully loaded the page.")
sleep(10)
#TODO: sleep here until drop time
print(timestamp()+"GO!")
category_xpath = find_deepest_xpath_containing(driver,json_input["category"])
category_elem = driver.find_element_by_xpath(category_xpath)
category_elem.click()
print(timestamp()+"clicked category")
'''
keywords = json_input["keywords"]
count = 0
for _ in range(0,30000):
    for word in keywords:
        if word in driver.page_source:
            count += 1
    if count == len(keywords):
        break
'''
print(dt.today())
xpaths_to_buy = []
for _ in range(0,30000):
    xpaths_to_buy = match_keywords_and_not_sold_out(driver.page_source,json_input["keywords"])
    if xpaths_to_buy is not None and len(xpaths_to_buy) > 0:
        break
print(timestamp()+"the xpaths to items we want to buy")
for xpath in xpaths_to_buy:
    print(xpath)
print(timestamp()+"found "+str(len(xpaths_to_buy))+" xpaths")
rand_index = randint(0,1000) % len(xpaths_to_buy)
#pick a random matching index
xpath = xpaths_to_buy[rand_index]
print(timestamp()+"clicking "+xpath)
element = driver.find_element_by_xpath(xpath)
element.click()
print(timestamp()+"clicked "+xpath)
print(timestamp()+"finding xpath to atc")
xpath_to_atc = None
elem = None
for _ in range(0,30000):
    xpath_to_atc = find_deepest_xpath_containing(driver,"add to cart")
    if xpath_to_atc is not None and len(xpath_to_atc) > len("/html/body/div"):
        elem = driver.find_element_by_xpath(xpath_to_atc)
        if elem.is_displayed():
            break
    sleep(0.01)
print(timestamp()+"found xpath to atc: "+xpath_to_atc)
#TODO: select size
print(timestamp()+"clicking atc")
elem.click()
checkout = None
# durability favored over speed. cpus are fast anyways
print(timestamp()+"waiting for check out button")
xpath_to_checkout = None
for _ in range(0,3000):
    xpath_to_checkout = find_deepest_xpath_containing(driver,"checkout")
    if xpath_to_checkout is not None:
        checkout = driver.find_element_by_xpath(xpath_to_checkout)
        try:
            if checkout.is_displayed(): break
        except:
            pass
    sleep(0.01)
print(timestamp()+"found visible xpath to checkout: "+xpath_to_checkout+", clicking...")
checkout.click()
for _ in range(0,30000):
    xpath_to_email = find_deepest_xpath_containing(driver,"address")
    xpath_to_address = find_deepest_xpath_containing(driver,"email")
    if None not in [xpath_to_email,xpath_to_address]:
        email = driver.find_element_by_xpath(xpath_to_email)
        address = driver.find_element_by_xpath(xpath_to_address)
        if email.is_displayed() and address.is_displayed():
            break
    sleep(0.01)
print(timestamp()+"we are on the checkout page! inputting data.")
#TODO: remove this safety measure
xpath_to_email = find_deepest_xpath_containing(driver,"email")
email_field = driver.find_element_by_xpath(xpath_to_address)
email_field.click()
press_shift_tab(driver)
send_keys(driver,json_input["bill"]["fname"])
send_keys(driver,Keys.SPACE)
send_keys(driver,json_input["bill"]["lname"])
press_tab(driver)
send_keys(driver,json_input["bill"]["email"])
press_tab(driver)
for char in json_input["bill"]["phone"]:
    send_keys(driver,char)
    sleep(0.01)
press_tab(driver)
send_keys(driver,json_input["bill"]["addy1"])
press_tab(driver)
send_keys(driver,json_input["bill"]["addy2"])
press_tab(driver)
send_keys(driver,json_input["bill"]["zip"])
press_tab(driver)
send_keys(driver,json_input["bill"]["city"])
press_tab(driver)
press_tab(driver)
press_tab(driver)
press_tab(driver)
send_keys(driver,json_input["ccdata"]["type"])
press_tab(driver)
for char in json_input["ccdata"]["number"]:
    sleep(0.01)
    send_keys(driver,char)
sleep(0.01)
press_tab(driver)
if len(json_input["ccdata"]["month"]) == 1:
    json_input=["ccdata"]["month"] = "0"+json_input["ccdata"]["month"]
send_keys(driver,json_input["ccdata"]["month"])
press_tab(driver)
send_keys(driver,json_input["ccdata"]["year"])
press_tab(driver)
send_keys(driver,json_input["ccdata"]["cvv"])
xpath_to_agreement = find_deepest_xpath_containing(driver,"have read and agree")
agreement = driver.find_element_by_xpath(xpath_to_agreement)
agreement.click()
print(timestamp()+"data input! clicking process payment!!")
for _ in range(0,30000):
    xpath_to_process = find_all_xpath_containing(driver,"process payment")
    process_button = driver.find_element_by_xpath(xpath_to_process)
    if process_button.is_displayed(): break
    sleep(0.01)
process_button.click()
sleep(60)
print("------------FINAL PAGE----------------")
print(driver.page_source)
print("------------FINAL PAGE----------------")
print(json_input["bill"]["email"])
#stop_container()








