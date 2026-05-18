import requests
from bs4 import BeautifulSoup
import time
import re
import json
from urllib.parse import urljoin
import random

BASE_URL = "https://hackenproof.com"
PROGRAMS_LIST_URL = f"{BASE_URL}/programs"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://hackenproof.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def get_program_links(max_pages=5):
    """Fetch program links from the listing pages"""
    all_links = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, max_pages + 1):
        url = f"{PROGRAMS_LIST_URL}?page={page}" if page > 1 else PROGRAMS_LIST_URL
        
        try:
            print(f"Fetching programs page {page}...")
            response = session.get(url, timeout=15)
            
            if response.status_code == 403:
                print("❌ Still getting 403. Try using a proxy or Selenium.")
                break
            elif response.status_code != 200:
                print(f"❌ Status code: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all program detail links
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/programs/') and len(href.split('/')) == 3:  # /programs/slug
                    full_url = urljoin(BASE_URL, href)
                    if full_url not in all_links:
                        all_links.append(full_url)

            print(f"   Found {len(all_links)} unique programs so far...")

            time.sleep(random.uniform(2, 4))  # Random delay between pages

        except Exception as e:
            print(f"Error on page {page}: {e}")
            break

    return all_links


def check_reputation_requirement(program_url, session):
    """Check if program requires reputation points"""
    try:
        time.sleep(random.uniform(1.5, 3.5))
        response = session.get(program_url, timeout=12)
        
        if response.status_code != 200:
            return {"url": program_url, "status": "blocked", "code": response.status_code}

        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()

        # Look for reputation requirement
        match = re.search(r'(\d+)\s*reputation points?\s*required', text)
        
        if match:
            points = int(match.group(1))
            return {
                "url": program_url,
                "requires_reputation": True,
                "points_required": points,
                "status": "requires_rep"
            }
        else:
            # Many programs don't mention it → usually 0
            return {
                "url": program_url,
                "requires_reputation": False,
                "points_required": 0,
                "status": "no_requirement"
            }

    except Exception as e:
        return {"url": program_url, "status": "error", "error": str(e)}


def main():
    print("🚀 Starting HackenProof no-reputation filter...\n")
    
    program_urls = get_program_links(max_pages=6)   # Change this number as needed
    
    if not program_urls:
        print("❌ Could not fetch any programs. Recommendations:")
        print("   1. Use a residential proxy")
        print("   2. Try Selenium + undetected-chromedriver")
        print("   3. Run the script from a different network / VPN")
        return

    print(f"\n✅ Found {len(program_urls)} programs. Now checking reputation requirement...\n")

    session = requests.Session()
    session.headers.update(HEADERS)

    no_rep_programs = []
    checked = 0

    for i, url in enumerate(program_urls, 1):
        print(f"[{i}/{len(program_urls)}] Checking → {url.split('/')[-1]}")
        result = check_reputation_requirement(url, session)
        checked += 1

        if result["status"] == "no_requirement":
            print("   ✅ NO reputation required!")
            no_rep_programs.append(result)
        elif result["status"] == "requires_rep":
            print(f"   → Requires {result['points_required']} reputation points")
        else:
            print(f"   → Skipped ({result.get('code') or result.get('error')})")

    with open("hackenproof_no_rep_programs.json", "w", encoding="utf-8") as f:
        json.dump(no_rep_programs, f, indent=2, ensure_ascii=False)

    print("\n" + "="*70)
    print(f"Finished! Checked {checked} programs.")
    print(f"Found {len(no_rep_programs)} programs that likely require **0 reputation**.")
    print("Results saved → hackenproof_no_rep_programs.json")

    if no_rep_programs:
        print("\nFirst 10 programs with no reputation requirement:")
        for p in no_rep_programs[:10]:
            print(f"• {p['url']}")


if __name__ == "__main__":
    main()
