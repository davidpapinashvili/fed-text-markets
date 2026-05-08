import requests
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import re
import time

BASE_URL = "https://www.federalreserve.gov"
ARCHIVE_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"

def get_statement_links():
    print ("Fetching statement links from the Federal Reserve website...")
    response = requests.get(ARCHIVE_URL, timeout=30)
    print("Archive page status:", response.status_code)
    response.raise_for_status()
 
    soup = BeautifulSoup(response.text, "lxml")
    
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = href if href.startswith("http") else BASE_URL + href

        if re.search(r"/newsevents/pressreleases/monetary\d{8}a\.htm", full_url):
            links.append(full_url)

    links = sorted(set(links))
    print("Number of statement links found:", len(links))
    print("First 5 links:", links[:5])
    return links

def extract_date_from_url(url):
    match = re.search(r"monetary(\d{8})a\.htm", url)
    if match:
        raw = match.group(1)
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    return ""

def scrape_statement(url):
    print(f"Opening statements page: {url}")
    response = requests.get(url, timeout=30)
    print("Statement page status:", response.status_code)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    title_tag = soup.find("title")
    title = title_tag.get_text(" ", strip=True) if title_tag else ""

    main_content = soup.find("div", class_="col-xs-12 col-sm-8 col-md-8")
    if main_content:
        paragraphs = [p.get_text(" ", strip=True) for p in main_content.find_all("p")]
    else:
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

    body_text = " ".join(paragraphs)
    body_text = body_text.replace("\n", " ").replace("\r", " ")
    
    date = extract_date_from_url(url)

    return {
        "date": date,
        "url": url,
        "title": title,
        "statement_text": body_text
    }

def is_standard_fomc_statement(row):
    """
    The Federal Reserve archive includes some non-standard releases under
    the same URL pattern, e.g. the quinquennial update to the Statement on
    Longer-Run Goals and Monetary Policy Strategy. Standard policy
    statements have the title 'Federal Reserve issues FOMC statement'.
    """
    title = str(row.get("title", "")).lower()
    return "issues fomc statement" in title


def main():
    print("Starting scraper...")
    output_path = Path("data/raw/fed_statements_raw.csv")
    print("Output path will be:", output_path.resolve())

    links = get_statement_links()

    rows = []
    for link in links:
        try:
            row = scrape_statement(link)
            rows.append(row)
            print("Scraped successfully.")
            time.sleep(0.5)  # be polite to the Fed's server
        except Exception as e:
            print(f"Failed: {link} | {e}")

    print("Rows collected:", len(rows))

    df = pd.DataFrame(rows)

    # Filter out non-standard releases (e.g. framework-review documents)
    before_filter = len(df)
    df["is_standard"] = df.apply(is_standard_fomc_statement, axis=1)
    excluded = df[~df["is_standard"]].copy()

    if not excluded.empty:
        print("\nExcluded non-standard releases:")
        print(excluded[["date", "title"]].to_string(index=False))

    df = df[df["is_standard"]].drop(columns=["is_standard"]).reset_index(drop=True)
    print(f"\nKept {len(df)} of {before_filter} releases as standard FOMC statements.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Saved {len(df)} statements to {output_path.resolve()}")

if __name__ == "__main__":
    main()