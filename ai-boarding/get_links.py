import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from typing import Union, List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st

@st.experimental_singleton
def get_driver():
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def filter_links(links_list: list[str]):
    word_list = ["terms", "refund", "cancel", "info", "about", "faq", "policy", "policies", "offerings"]

    # Function to check if a string contains any word from the word list
    def contains_word(string, word_list):
        return any(word in string for word in word_list)

    # Filter strings that contain at least one word from the word list and add the parent link
    urls = [string for string in links_list if contains_word(string, word_list) and ".pdf" not in string]
    return urls


def convert_to_dict(links_list: list[str], website_link):
    urls = [{"url": website_link}] + [{"url": string} for string in links_list]
    return urls

def get_links(website_link: str) -> List:
    """
    get all sub-URLs in a given URL with maximum depth of 1
    :param website_link: parent URL
    :return: a list of URLs
    """
    source = "BeautifulSoup"
    # create empty dict to not repeat the same link
    dict_href_links = {}

    # get html data
    html_data = requests.get(website_link).text #getdata(website_link)
    soup = BeautifulSoup(html_data, "html.parser")
    list_links = []
    for link in soup.find_all("a", href=True):

        # Append to list if new link contains original link
        if "http" in str(link["href"]):
            list_links.append(link["href"])

        # Include all href that do not start with website link but with "/"
        if str(link["href"]).startswith("/"):
            if link["href"] not in dict_href_links:
                dict_href_links[link["href"]] = None
                link_with_www = website_link + link["href"][1:]
                list_links.append(link_with_www)

    if len(list_links) > 0:
        list_links = filter_links(list_links)

    if len(list_links) == 0:
        source="selenium"
        options = Options()
        options.add_argument('--disable-gpu')
        options.add_argument('--headless')
        driver = get_driver()
        # driver = webdriver.Chrome()  # You need to have Chrome WebDriver installed
        driver.get(website_link)
        list_links = [element.get_attribute("href") for element in
                 driver.find_elements(By.CSS_SELECTOR, "a[href*=terms], a[href*=refund], a[href*=cancel], "
                                                       "a[href*=info], a[href*=about], a[href*=faq], "
                                                       "a[href*=policy], a[href*=policies], a[href*=offerings]")]
        driver.quit()

    search_links = [link for link in list_links if "terms" in link or "polic" in link]
    for link in search_links:
        driver = webdriver.Chrome()  # You need to have Chrome WebDriver installed
        driver.get(link)
        list_links = list_links + [element.get_attribute("href") for element in
                      driver.find_elements(By.CSS_SELECTOR, "a[href*=refund], a[href*=cancel]")]
        driver.quit()

    # remove duplicates
    list_links = list(set(list_links))

    links = convert_to_dict(list_links, website_link)
    return links, source
