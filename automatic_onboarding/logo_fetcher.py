from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin
import requests
from io import BytesIO
from PIL import Image
import logging
import serpapi
logging.basicConfig(level=logging.INFO)
from typing import List

# needed locally
import os
from dotenv import load_dotenv
load_dotenv()


def fetch_logo(url: str, merchant_name: str, logos_limit: int = 1):
    output_images, output_paths = fetch_logo_with_serpapi(url, merchant_name, logos_limit)
    if output_images is None or len(output_images) == 0:
        output_images, output_paths = fetch_logo_with_selenium(url, merchant_name, logos_limit)
    return output_images, output_paths


def fetch_logo_with_serpapi(url: str, merchant_name: str, logos_limit: int = 1, engine: str = "google_images"):
    try:
        params = {
            "engine": engine,
            "q": f"{merchant_name} logo",
        }
        client = serpapi.Client(api_key=os.getenv("SERP_API_KEY"))
        results = client.search(params)
        images_results = results['images_results']
        images_urls = [img_result['thumbnail'] for img_result in images_results]
        logging.info(f"Used serpapi with engine {engine}. Found {len(images_urls)} urls")
    except Exception as e:
        logging.info(f"could not find logos: {e}")
        return None, None

    output_images, output_paths = _download_and_save_images(images_urls[:logos_limit])
    return output_images, output_paths


def fetch_logo_with_selenium(url: str, merchant_name: str, logos_limit: int = 1):
    try:
        # Setup Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Open the website
        driver.get(url)

        # Attempt to find the logo in common places
        logo_urls = []

        # Fallback to favicon
        try:
            if len(logo_urls) < logos_limit:
                icon_link = driver.find_element(By.XPATH, "//link[@rel='icon']")
                if icon_link:
                    logo_url = icon_link.get_attribute('href')
                    if logo_url is not None:
                        logo_urls.append(logo_url)
        except Exception as e:
            logging.info(f"got exception in favicon step: {e}")
        logging.info(f"After favicon step: {len(logo_urls)} urls")

        # Search for <img> tags with potential keywords
        keywords = ['logo', 'icon', merchant_name.lower()]
        keyword_images = driver.find_elements(By.TAG_NAME, 'img')
        # Add images from header and footer
        headers = driver.find_elements(By.CSS_SELECTOR, 'header img')
        footers = driver.find_elements(By.CSS_SELECTOR, 'footer img')
        images = headers+footers+keyword_images
        logging.info(f"Found {len(images)} total images. In Header: {len(headers)}. In footer: {len(footers)}. in keywords: {len(keyword_images)}")

        for img in images:
            src = img.get_attribute('src')
            alt = img.get_attribute('alt')
            class_name = img.get_attribute('class')
            if any(keyword in (src or '').lower() for keyword in keywords) or \
                    any(keyword in (alt or '').lower() for keyword in keywords) or \
                    any(keyword in (class_name or '').lower() for keyword in keywords):
                logo_urls.append(src)
                if len(logo_urls) >= logos_limit:
                    break
        logging.info(f"After images scan step: {len(logo_urls)} urls")

        # Check specific CSS classes or IDs for logos
        if len(logo_urls) < logos_limit:
            potential_logo_elements = driver.find_elements(By.CSS_SELECTOR, '[id*="logo"], [class*="logo"]')
            for element in potential_logo_elements:
                logo_url = element.get_attribute('src') or element.get_attribute('href')
                if logo_url:
                    logo_urls.append(logo_url)
                    if len(logo_urls) >= logos_limit:
                        break
        logging.info(f"After third step: {len(logo_urls)} urls")

        # Construct the full URL if necessary
        if len(logo_urls) >= 0:
            logo_urls = [logo_url if logo_url.startswith('http') else urljoin(url, logo_url) for logo_url in logo_urls]
        # if logo_url and not logo_url.startswith('http'):
        #     logo_url = urljoin(url, logo_url)

        if len(logo_urls) >= 0:
            output_images, output_paths = _download_and_save_images(logo_urls)
            driver.quit()
            return output_images, output_paths
        else:
            driver.quit()
            return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None


def _download_and_save_images(images_urls: List[str]):
    output_images, output_paths = [], []
    for i, logo_url in enumerate(images_urls):
        try:
            # Download the logo image
            logo_response = requests.get(logo_url)
            logo_response.raise_for_status()

            # Open the image and convert it to JPEG
            image = Image.open(BytesIO(logo_response.content))
            logo_filename = f"{merchant_name}_logo{i}.jpeg"
            image.convert("RGB").save(logo_filename, "JPEG")
            output_paths.append(logo_filename)
            output_images.append(image.convert("RGB"))
        except Exception as e:
            logging.info(f"processing error in image {i}: {e}")
    return output_images, output_paths


if __name__ == "__main__":
    # Example usage
    url = "https://www.workiz.com/"  # "https://www.example.com"
    merchant_name = "workiz"
    img, logo_file = fetch_logo(url, merchant_name, 10)
    if logo_file:
        print(f"Logo saved as {logo_file}")
    else:
        print("Logo not found")
