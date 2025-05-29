# 📦 Amazon Review Scraper

A web-based tool to scrape product reviews from [Amazon.in](https://www.amazon.in) using **Flask** and **Selenium**, and export them as a structured JSON file.

---

## 🚀 Features

- 🔍 Scrapes reviews from any Amazon.in product page using its URL
- 🧠 Extracts:
  - Review Date (in `dd/mm/yyyy` format)
  - Review Title
  - Review Body
  - User Rating (out of 5)
- 📄 Saves all reviews to a downloadable JSON file
- 🧭 Uses user-specific browser profiles to persist login
- 🔐 Supports manual login to handle CAPTCHA or authentication

---

## 🖼️ Sample Output (JSON)

```json
[
  {
    "Review_Date": "18/05/2025",
    "User_Rating_out_of_5": "4",
    "Review_Title": "Great product!",
    "Review_Body": "The quality was better than expected. Delivery was quick too."
  }
]

