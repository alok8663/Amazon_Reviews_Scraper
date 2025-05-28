from flask import Flask, render_template, request, send_file
import os

app = Flask(__name__)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv
import re

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_reviews(asin, max_pages):
    driver = init_driver()
    filename = f"amazon_reviews_{asin}.csv"
    output_file = open(filename, mode="w", newline='', encoding="utf-8")
    writer = csv.writer(output_file)
    writer.writerow(["User_Rating_out_of_5", "Review_Title", "Review_Body"])

    try:
        url = f"https://www.amazon.in/product-reviews/{asin}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
        driver.get(url)
        print("Waiting for login if needed...")
        time.sleep(60)  # Time for manual login if required

        page = 1
        while page <= max_pages:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".review")))
            reviews = driver.find_elements(By.CSS_SELECTOR, ".review")

            for r in reviews:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", r)
                    time.sleep(0.1)

                    # Extract rating
                    try:
                        rating_element = r.find_element(By.CSS_SELECTOR, "i[data-hook='review-star-rating'], i[data-hook='cmps-review-star-rating']")
                        rating_text = rating_element.get_attribute('textContent').strip()
                        rating_match = re.search(r"(\d+\.?\d*) out of 5", rating_text)
                        rating = rating_match.group(1) if rating_match else "N/A"
                    except Exception as e:
                        print("Rating extraction error:", e)
                        rating = "N/A"

                    # Extract title
                    try:
                        title = r.find_element(By.CSS_SELECTOR, ".a-size-base.a-link-normal.review-title.a-color-base.review-title-content.a-text-bold").text.strip()
                    except:
                        title = "N/A"

                    # Extract body
                    try:
                        body = "N/A"
                        try:
                            review_body_container = r.find_element(By.CSS_SELECTOR, "span[data-hook='review-body']")
                            direct_text = review_body_container.text.strip()
                            if direct_text:
                                body = direct_text
                            else:
                                span_children = review_body_container.find_elements(By.TAG_NAME, "span")
                                for s in span_children:
                                    text = s.text.strip()
                                    if text:
                                        body = text
                                        break
                        except Exception as e1:
                            print("Standard/video review body structure not matched:", e1)

                        if body == "N/A":
                            try:
                                username_element = None
                                try:
                                    username_element = r.find_element(By.CSS_SELECTOR, "span.a-profile-name")
                                except:
                                    pass
                                
                                candidates = r.find_elements(By.CSS_SELECTOR, "div.a-row, span")
                                for c in candidates:
                                    if username_element and username_element.is_displayed():
                                        if c == username_element or c.find_elements(By.XPATH, ".//ancestor-or-self::*[contains(@class, 'a-profile-content')]"):
                                            continue
                                    
                                    text = c.text.strip()
                                    if text and not any(kw in text.lower() for kw in ["reviewed in", "verified purchase", "report", "helpful", "video", "click", "reader", "customer"]):
                                        body = text
                                        break
                            except Exception as fallback_error:
                                print("Fallback body extraction failed:", fallback_error)
                    except Exception as main_error:
                        print("Review body extraction error:", main_error)
                        body = "N/A"

                    if body != "N/A":
                        body = body.replace("Click to play video", "").strip()
                        if not body:
                            body = "N/A"

                    writer.writerow([rating, title, body])
                except Exception as e:
                    print("Error parsing a review:", e)
                    continue

            try:
                next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "li.a-last a")))
                driver.execute_script("arguments[0].click();", next_button)
                page += 1
                time.sleep(3)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            except:
                print("No more pages or next button not found.")
                break
    finally:
        output_file.close()

    return filename

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        asin = request.form.get('asin')
        pages = int(request.form.get('pages', 1))
        if not asin:
            return render_template("index.html", error="Please enter a valid ASIN")

        try:
            csv_filename = scrape_reviews(asin, pages)
            return send_file(csv_filename, as_attachment=True)
        except Exception as e:
            return render_template("index.html", error=f"An error occurred: {str(e)}")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
