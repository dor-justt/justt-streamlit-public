from typing import List, Tuple, Dict
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


def convert_to_apify_urls_dict(links_list: List[str], website_link: str) -> List[Dict[str, str]]:
    """
    Converts the website link, and the list of child links to a list of dictionaries, as required to use Apify
    :param links_list: list of urls
    :param website_link: single url
    :return: List as described
    """
    urls = [{"url": website_link}] + [{"url": string} for string in links_list]
    return urls


def get_links(website_link: str) -> Tuple[List, str]:
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

    # take all the pages with based on the css string
    if len(list_links) == 0:
        driver = webdriver.Chrome(options=options)
        driver.get(website_link)
        list_links = [element.get_attribute("href") for element in driver.find_elements(By.CSS_SELECTOR, css_string)]
        driver.quit()
    print(f"len(list_links) 1: {len(list_links)}")

    # remove pages with irrelevant signs, sinse they are usually child pages of what we need
    chars = ['=', '?', '&', '%']
    list_links = [link for link in list_links if all(char not in link for char in chars)]
    print(f"len(list_links) 2: {len(list_links)}")

    # remove duplicates
    if len(list_links) > 0:
        list_links = list(set(list_links))
    print(f"len(list_links) 3: {len(list_links)}")

    # take maximum two from each keyword
    res_links = []
    for key_word in key_words:
        res_links.extend(sorted([link for link in list_links if key_word in link], key=len)[:2])
    list_links = list(set(res_links))
    print(f"len(list_links) 4: {len(list_links)}")
    print(list_links)

    links = convert_to_apify_urls_dict(list_links, website_link)
    return links, source
