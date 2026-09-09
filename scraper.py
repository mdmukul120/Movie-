import json
import re
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://ftp.ctgfun.com/"

def extract_media_data():
    results = []

    with sync_playwright() as p:
        # Chromium ব্রাউজার হেডলেস মোডে রান করা
        browser = p.chromium.launch(headless=True)
        # রিয়েল ইউজারের মতো আচরণ করার জন্য User-Agent সেট করা
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, impervious) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print(f"মেইন পেজে প্রবেশ করা হচ্ছে: {BASE_URL}")
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3) # জাভাস্ক্রিপ্ট লোড হওয়ার জন্য সাময়িক বিরতি
        except Exception as e:
            print(f"পেজ লোড হতে সমস্যা হয়েছে: {e}")
            browser.close()
            return

        # হোমপেজের সমস্ত লিংক (Slugs) সংগ্রহ
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # সাইটের সমস্ত স্লোগ / পোস্টের লিংক ফিল্টার
        slug_links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if BASE_URL in href or href.startswith('/'):
                if not any(x in href for x in ['#', 'javascript:', 'login', 'register']):
                    full_url = href if href.startswith('http') else BASE_URL.rstrip('/') + href
                    slug_links.add(full_url)

        print(f"মোট {len(slug_links)}টি লিংকের তালিকা পাওয়া গেছে। স্ক্যানিং শুরু হচ্ছে...")

        # প্রতিটি স্লোগ পেজ থেকে মিডিয়া বের করা
        for idx, slug_url in enumerate(slug_links, 1):
            print(f"[{idx}/{len(slug_links)}] তথ্য স্ক্র্যাপ করা হচ্ছে: {slug_url}")
            try:
                # পেজে সরাসরি না গিয়ে নেটওয়ার্ক রেসপন্স ইন্টারসেপ্ট করা
                slug_page = context.new_page()
                
                # পপ-আপ অ্যাড ও রিডাইরেক্ট ব্লক করার জন্য নির্দিষ্ট স্ক্রিপ্ট
                slug_page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "stylesheet", "font"] and "google" in route.request.url else route.continue_())

                slug_page.goto(slug_url, wait_until="networkidle", timeout=30000)
                
                # টাইটেল বের করা
                title = slug_page.title()
                
                # থাম্বনেইল/পোস্টার ইমেজ বের করা
                page_soup = BeautifulSoup(slug_page.content(), 'html.parser')
                img_tag = page_soup.find('meta', property='og:image') or page_soup.find('img')
                image_url = img_tag['content'] if img_tag and img_tag.has_attr('content') else (img_tag['src'] if img_tag and img_tag.has_attr('src') else "")

                # MP4 লিংক অনুসন্ধান
                mp4_links = set()
                
                # HTML ট্যাগ বা জাভাস্ক্রিপ্ট সোর্স থেকে .mp4 ইউআরএল ফিল্টার
                matches = re.findall(r'https?://[^\s"\']+\.mp4', slug_page.content())
                for match in matches:
                    mp4_links.add(match)

                # video / source ট্যাগ থেকে লিংক খোঁজা
                for video in page_soup.find_all(['video', 'source']):
                    src = video.get('src')
                    if src and '.mp4' in src:
                        full_mp4 = src if src.startswith('http') else BASE_URL.rstrip('/') + src
                        mp4_links.add(full_mp4)

                if mp4_links:
                    results.append({
                        "title": title.strip(),
                        "slug_url": slug_url,
                        "image_url": image_url,
                        "mp4_videos": list(mp4_links)
                    })
                    print(f"   -> সফল! {len(mp4_links)} টি MP4 ভিডিও পাওয়া গেছে।")

                slug_page.close()
            except Exception as err:
                print(f"   -> ত্রুটি ({slug_url}): {err}")
                continue

        browser.close()

    # ডাটা JSON ফাইলে সংরক্ষণ
    with open("scraped_videos.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    
    print("\nস্ক্র্যাপিং সম্পন্ন হয়েছে! 'scraped_videos.json' ফাইলে ফলাফল সেভ করা হয়েছে।")

if __name__ == "__main__":
    extract_media_data()
