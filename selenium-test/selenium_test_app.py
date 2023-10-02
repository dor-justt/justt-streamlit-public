import streamlit as st
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


def run_selenium():
    url = "https://www.oyorooms.com/"
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    list_links = [element.get_attribute("href") for element in
             driver.find_elements(By.CSS_SELECTOR, "a[href*=terms], a[href*=refund], a[href*=cancel], "
                                                   "a[href*=info], a[href*=about], a[href*=faq], "
                                                   "a[href*=policy], a[href*=policies], a[href*=offerings]")]
    driver.quit()
    return list_links


if __name__ == "__main__":
    st.set_page_config(page_title="Selenium Test", page_icon='✅', initial_sidebar_state='collapsed')
    st.title('🔨 Selenium Test for Streamlit Sharing')
    st.markdown('''This app is only a very simple test for **Selenium** running on **Streamlit Sharing** runtime.<br>
        The suggestion for this demo app came from a post on the Streamlit Community Forum.<br>
        <https://discuss.streamlit.io/t/issue-with-selenium-on-a-streamlit-app/11563><br>
        This is just a very very simple example and more a proof of concept.
        A link is called and waited for the existence of a specific class and read it.
        If there is no error message, the action was successful.
        Afterwards the log file of chromium is read and displayed.
        ---
        ''', unsafe_allow_html=True)

    if st.button('Start Selenium run'):
        st.info('Selenium is running, please wait...')
        result = run_selenium()
        st.info(f'Result -> {result}')
        st.info('Successful finished. Selenium log file is shown below...')
