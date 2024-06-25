# import requests
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.common.by import By
from typing import Union, List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-features=NetworkService")
options.add_argument("--window-size=1920x1080")
options.add_argument("--disable-features=VizDisplayCompositor")


def filter_links(links_list: List[str]):
    word_list = ["terms", "refund", "cancel", "info", "about", "faq", "policy", "policies", "offerings", "shipping"]

    # Function to check if a string contains any word from the word list
    def contains_word(string, word_list):
        return any(word in string for word in word_list)

    # Filter strings that contain at least one word from the word list and add the parent link
    urls = [string for string in links_list if contains_word(string, word_list) and ".pdf" not in string]
    return urls


def convert_to_dict(links_list: List[str], website_link):
    urls = [{"url": website_link}] + [{"url": string} for string in links_list]
    return urls


def get_links(website_link: str) -> List:
    """
    get all sub-URLs in a given URL with maximum depth of 1
    :param website_link: parent URL
    :return: a list of URLs
    """
    list_links = []
    # source = "BeautifulSoup"
    # # create empty dict to not repeat the same link
    # dict_href_links = {}
    #
    # # get html data
    # html_data = requests.get(website_link).text #getdata(website_link)
    # soup = BeautifulSoup(html_data, "html.parser")
    # for link in soup.find_all("a", href=True):
    #
    #     # Append to list if new link contains original link
    #     if "http" in str(link["href"]):
    #         list_links.append(link["href"])
    #
    #     # Include all href that do not start with website link but with "/"
    #     if str(link["href"]).startswith("/"):
    #         if link["href"] not in dict_href_links:
    #             dict_href_links[link["href"]] = None
    #             link_with_www = website_link + link["href"][1:]
    #             list_links.append(link_with_www)
    #
    # if len(list_links) > 0:
    #     list_links = filter_links(list_links)

    if len(list_links) == 0:
        source = "selenium"
        driver = webdriver.Chrome(options=options)
        driver.get(website_link)
        list_links = [element.get_attribute("href") for element in
                 driver.find_elements(By.CSS_SELECTOR, "a[href*=terms], a[href*=refund], a[href*=cancel], "
                                                       "a[href*=about], a[href*=faq], "
                                                       "a[href*=policy], a[href*=policies], a[href*=offerings]")]
        driver.quit()

    search_links = [link for link in list_links if "terms" in link or "polic" in link]
    for link in search_links:
        driver = webdriver.Chrome(options=options)
        driver.get(link)
        list_links = list_links + [element.get_attribute("href") for element in
                      driver.find_elements(By.CSS_SELECTOR, "a[href*=refund], a[href*=cancel], a[href*=return]")]
        driver.quit()

    if len(list_links) > 0:
        # remove duplicates
        list_links = list(set(list_links))

    if len(list_links) > 10:
        list_links = [link for link in list_links if
               ("terms" in link) or ("refund" in link) or ("return" in link) or ("polic" in link)]

    links = convert_to_dict(list_links, website_link)
    return links, source
