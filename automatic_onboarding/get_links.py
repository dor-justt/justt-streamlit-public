from typing import List, Tuple
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
    word_list = ["terms", "refund", "cancel", "info", "about", "faq", "policy", "policies", "offerings", "shipping", "store", "contact"]

    # Function to check if a string contains any word from the word list
    def contains_word(string, word_list):
        return any(word in string for word in word_list)

    # Filter strings that contain at least one word from the word list and add the parent link
    urls = [string for string in links_list if contains_word(string, word_list) and ".pdf" not in string]
    return urls


def convert_to_dict(links_list: List[str], website_link):
    urls = [{"url": website_link}] + [{"url": string} for string in links_list]
    return urls


def get_links(website_link: str, max_links = 10) -> Tuple[List, str]:
    """
    get all sub-URLs in a given URL with maximum depth of 1
    :param website_link: parent URL
    :return: a list of URLs
    """
    key_words = ["terms", "refund", "cancel", "info", "about", "faq", "polic", "offerings", "shipping", "store", "contact"]
    css_string = "a[href*=terms], a[href*=refund], a[href*=cancel], a[href*=about], a[href*=faq], a[href*=policy], a[href*=policies], " \
                 "a[href*=offerings], a[href*=contact], a[href*=info], a[href*=support], a[href*=store]"
    list_links = []
    source = "selenium"

    if len(list_links) == 0:
        driver = webdriver.Chrome(options=options)
        driver.get(website_link)
        list_links = [element.get_attribute("href") for element in driver.find_elements(By.CSS_SELECTOR, css_string)]
        driver.quit()
    print(f"len(list_links) 1: {len(list_links)}")
    chars = ['=', '?', '&', '%']
    list_links = [link for link in list_links if all(char not in link for char in chars)]

    print(f"len(list_links) 2: {len(list_links)}")
    # remove duplicates
    if len(list_links) > 0:
        list_links = list(set(list_links))
    res_links = []
    print(f"len(list_links) 3: {len(list_links)}")
    # take maximum two from each keyword
    for key_word in key_words:
        res_links.extend(sorted([link for link in list_links if key_word in link], key=len)[:2])
    list_links = list(set(res_links))
    print(f"len(list_links) 4: {len(list_links)}")
    print(list_links)

    links = convert_to_dict(list_links, website_link)
    return links, source
