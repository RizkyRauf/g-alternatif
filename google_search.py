#!/usr/bin/env python3
"""
Standalone Scraper Script - Untuk dijalankan via subprocess
Event loop terisolasi total - tidak konflik dengan FastAPI/uvloop
Bisa dipanggil langsung: python google_search.py --query pertamina --pages 3 --json
"""

from seleniumbase import SB
from bs4 import BeautifulSoup
import argparse
import json
import time
import random
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Konfigurasi default
BASE_URL = "https://searx.kavin.rocks/search"
DEFAULT_QUERY = "pertamina"
DEFAULT_PAGES = 3
DEFAULT_DELAY = 2.0


class SearchResult:
    """Simple data class untuk hasil (tanpa Pydantic dependency)"""
    def __init__(self, title: str, url: str, domain: str, content: str, 
                 engine: str, page_number: int, worker_id: int):
        self.title = title
        self.url = url
        self.domain = domain
        self.content = content
        self.engine = engine
        self.page_number = page_number
        self.worker_id = worker_id
        self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "domain": self.domain,
            "content": self.content,
            "engine": self.engine,
            "page_number": self.page_number,
            "worker_id": self.worker_id,
            "scraped_at": self.scraped_at
        }


def build_params(query: str, page_no: int) -> dict:
    """Bangun parameter pencarian SearX"""
    return {
        "q": query,
        "language": "id-ID",
        "time_range": "day",
        "safesearch": "0",
        "pageno": str(page_no),
        "categories": "general",
        "_": str(int(time.time() * 1000))
    }


def build_url(query: str, page_no: int) -> str:
    """Bangun URL lengkap"""
    params = build_params(query, page_no)
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{BASE_URL}?{query_string}"


def extract_results(html: str, page_number: int, worker_id: int) -> List[SearchResult]:
    """Ekstrak hasil dari HTML menggunakan BeautifulSoup"""
    results = []
    soup = BeautifulSoup(html, 'lxml')
    
    for article in soup.select("article.result"):
        try:
            title_el = article.select_one("h3 a")
            title = title_el.get_text(strip=True) if title_el else ""
            url = title_el.get("href") if title_el else ""
            
            domain_el = article.select_one("span.url_i1")
            domain = domain_el.get_text(strip=True) if domain_el else ""
            
            content_el = article.select_one("p.content")
            content = ""
            if content_el:
                for span in content_el.select("span.highlight"):
                    span.unwrap()
                content = content_el.get_text(strip=True)
            
            engine_el = article.select_one("div.engines span:first-child")
            engine = engine_el.get_text(strip=True) if engine_el else "unknown"
            
            if title or url:
                results.append(SearchResult(
                    title=title, url=url, domain=domain,
                    content=content, engine=engine,
                    page_number=page_number, worker_id=worker_id
                ))
        except Exception as e:
            print(f"Parse error: {e}", file=sys.stderr)
            continue
    
    return results


def perform_search(query: str, max_pages: int, worker_id: int = 0) -> List[dict]:
    """
    Fungsi scraping utama - dijalankan di subprocess terisolasi
    UC Mode dengan CDP auto-activation TIDAK MASALAH karena event loop terpisah
    """
    all_results = []
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    chromium_args = [
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--user-agent={random.choice(user_agents)}"
    ]
    
    with SB(
        uc=True,
        headless=True,
        block_images=True,
        disable_csp=True,
        incognito=True,
        disable_js=False,
        chromium_arg=chromium_args
    ) as sb:
        
        for page_no in range(1, max_pages + 1):
            url = build_url(query, page_no)
            print(f"Page {page_no}/{max_pages}: {url[:100]}...", file=sys.stderr)
            
            try:
                sb.open(url)
                
                sb.wait_for_element("article.result", timeout=25000)
                
                time.sleep(random.uniform(1.0, 2.5))
                
                html = sb.get_page_source()
                page_results = extract_results(html, page_no, worker_id)
                all_results.extend([r.to_dict() for r in page_results])
                
                print(f"Page {page_no}: {len(page_results)} results", file=sys.stderr)
                
            except Exception as e:
                print(f"Error page {page_no}: {e}", file=sys.stderr)
                continue
            
            if page_no < max_pages:
                delay = DEFAULT_DELAY + random.uniform(0.5, 2.0)
                time.sleep(delay)
    
    return all_results


def main():
    """Entry point untuk CLI / subprocess"""
    parser = argparse.ArgumentParser(description="SearX Scraper - Standalone")
    parser.add_argument("--query", "-q", default=DEFAULT_QUERY, help="Kata kunci pencarian")
    parser.add_argument("--pages", "-p", type=int, default=DEFAULT_PAGES, help="Jumlah halaman (1-10)")
    parser.add_argument("--worker-id", "-w", type=int, default=0, help="Worker ID untuk tracking")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON ke stdout")
    parser.add_argument("--output", "-o", help="Simpan hasil ke file JSON")
    
    args = parser.parse_args()
    
    if args.pages < 1 or args.pages > 20:
        print(f"Error: --pages harus antara 1-20", file=sys.stderr)
        sys.exit(1)
    
    print(f" Starting scraper: query='{args.query}', pages={args.pages}, worker_id={args.worker_id}", 
          file=sys.stderr)
    
    start = time.time()
    results = perform_search(args.query, args.pages, args.worker_id)
    elapsed = time.time() - start
    
    # Output
    output_data = {
        "query": args.query,
        "worker_id": args.worker_id,
        "pages_scraped": args.pages,
        "results_count": len(results),
        "duration_seconds": round(elapsed, 2),
        "results": results
    }
    
    if args.json or args.output:
        json_output = json.dumps(output_data, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f" Saved to '{args.output}'", file=sys.stderr)
        else:
            print(json_output)
    else:
        print(f"\n Done in {elapsed:.2f}s | Total: {len(results)} results", file=sys.stderr)
        if results:
            print("\n Preview:", file=sys.stderr)
            for i, item in enumerate(results[:3], 1):
                print(f"{i}. {item['title'][:60]}... [{item['domain']}]", file=sys.stderr)
    
    return output_data


if __name__ == "__main__":
    main()