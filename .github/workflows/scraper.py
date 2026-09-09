name: ViralLink2 Video Scraper

on:
  schedule:
    # প্রতি ২৪ ঘণ্টায় একবার অটোমেটিক রান হবে (ইউটিসি টাইম অনুযায়ী)
    - cron: '0 0 * * *'
  workflow_dispatch: # গিটহাব থেকে ম্যানুয়ালি রান করার অপশন

jobs:
  scrape:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout Repository
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install Dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        playwright install chromium
        playwright install-deps

    - name: Run Scraper Script
      run: |
        python scraper.py

    - name: Commit and Push Results
      run: |
        git config --global user.name "github-actions[bot]"
        git config --global user.email "github-actions[bot]@users.noreply.github.com"
        git add scraped_videos.json
        git commit -m "Automated update: Scraped MP4 links and metadata" || exit 0
        git push
