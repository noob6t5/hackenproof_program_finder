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

def get_program_links(max_pages=6):
    """Fetch program links from the listing pages"""
    all_links = []
    session = requests.Session()
    session.headers.update(HEADERS)
    
    print("🚀 Fetching program list...")
    for page in range(1, max_pages + 1):
        url = f"{PROGRAMS_LIST_URL}?page={page}" if page > 1 else PROGRAMS_LIST_URL
       
        try:
            response = session.get(url, timeout=15)
           
            if response.status_code == 403:
                print("❌ Got 403 Forbidden. Consider using a proxy or Selenium.")
                break
            elif response.status_code != 200:
                print(f"❌ Status code: {response.status_code}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
           
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/programs/') and len(href.split('/')) == 3:  # /programs/slug
                    full_url = urljoin(BASE_URL, href)
                    if full_url not in all_links:
                        all_links.append(full_url)
            
            print(f"  Page {page}: {len(all_links)} unique programs so far...")
            time.sleep(random.uniform(2, 4))
            
        except Exception as e:
            print(f"Error on page {page}: {e}")
            break
            
    print(f"✅ Total programs found: {len(all_links)}\n")
    return all_links


def check_program(program_url, session):
    """Check reputation requirement AND submission fee"""
    try:
        time.sleep(random.uniform(1.5, 3.5))
        response = session.get(program_url, timeout=12)
       
        if response.status_code != 200:
            return {"url": program_url, "status": "blocked", "code": response.status_code}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text().lower()
        
        # Reputation check
        rep_match = re.search(r'(\d+)\s*reputation points?\s*required', text)
        requires_rep = bool(rep_match)
        points = int(rep_match.group(1)) if rep_match else 0
        
        # Submission fee check 
        fee_match = re.search(r'\$\s*(\d+)\s*submission fee', text)
        has_fee = bool(fee_match)
        fee_amount = int(fee_match.group(1)) if fee_match else 0
        
        result = {
            "url": program_url,
            "requires_reputation": requires_rep,
            "points_required": points,
            "has_submission_fee": has_fee,
            "fee_amount": fee_amount,
            "status": "good" if not requires_rep and not has_fee else "filtered"
        }
        
        return result
        
    except Exception as e:
        return {"url": program_url, "status": "error", "error": str(e)}


def main():
    print("🚀 Starting HackenProof Free Submission Filter (No Rep + No Fee)...\n")
   
    program_urls = get_program_links(max_pages=6)
   
    if not program_urls:
        print("❌ Could not fetch programs. Try proxy / VPN / Selenium.")
        return

    print("🔍 Now checking each program for reputation & submission fee...\n")
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    free_programs = []
    checked = 0
    
    for i, url in enumerate(program_urls, 1):
        slug = url.split('/')[-1]
        print(f"[{i:3d}/{len(program_urls)}] Checking {slug}")
        
        result = check_program(url, session)
        checked += 1
        
        if result["status"] == "good":
            print("   ✅ FREE TO SUBMIT (no rep, no fee)")
            free_programs.append(result)
        elif result.get("has_submission_fee"):
            print(f"   💰 Has ${result.get('fee_amount', '?')} submission fee")
        elif result.get("requires_reputation"):
            print(f"   🔒 Requires {result.get('points_required', '?')} reputation")
        else:
            print(f"   ⚠️  Skipped ({result.get('status')})")
    
    # Save results
    with open("hackenproof_free_submission_programs.json", "w", encoding="utf-8") as f:
        json.dump(free_programs, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print(f"✅ FINISHED! Checked {checked} programs.")
    print(f"🎯 Found {len(free_programs)} programs that require **NO reputation** and have **NO submission fee**.")
    print("📁 Results saved to: hackenproof_free_submission_programs.json")
    
    if free_programs:
        print("\n🔗 Programs you can submit to for free:")
        for p in free_programs:
            print(f"• {p['url']}")
        
        print(f"\n💡 Tip: You can open these links directly in your browser.")
    else:
        print("\nNo free programs found in this run. Try increasing max_pages or run again later.")


if __name__ == "__main__":
    main()
