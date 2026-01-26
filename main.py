import os
from playwright.sync_api import Page, sync_playwright

LOGIN_URL = "http://admin.iot.kuaimai.com/login"
DEFAULT_PHONE = "13826056942"
DEFAULT_PASSWORD = "666666"


def login(page: Page) -> None:
    phone = os.getenv("KM_PHONE", DEFAULT_PHONE)
    password = os.getenv("KM_PASSWORD", DEFAULT_PASSWORD)

    page.goto(LOGIN_URL, wait_until="domcontentloaded")

    password_tab = page.get_by_text("密码登录")
    if password_tab.count() > 0:
        password_tab.first.click()

    page.wait_for_selector("input[placeholder='请输入手机号']")
    phone_input = page.locator("input[placeholder='请输入手机号']:visible").first
    password_input = page.locator("input[placeholder='请输入密码']:visible").first

    phone_input.click()
    phone_input.evaluate("el => el.removeAttribute('readonly')")
    phone_input.fill(phone)

    password_input.click()
    password_input.evaluate("el => el.removeAttribute('readonly')")
    password_input.fill(password)

    page.get_by_role("button", name="登录").click()
    page.wait_for_load_state("networkidle")


def run() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        page = browser.new_page()
        login(page)
        page.pause()  # keep the window open for inspection
        browser.close()


def test_login(page: Page) -> None:
    login(page)


if __name__ == "__main__":
    run()
