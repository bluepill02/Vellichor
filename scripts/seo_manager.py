import requests
import os
import sys
from urllib.parse import urljoin
from requests.exceptions import RequestException

WP_SITE_URL = os.getenv('WP_SITE_URL')
USERNAME = os.getenv('WP_USERNAME')
PASSWORD = os.getenv('WP_APP_PASSWORD')

if not all([WP_SITE_URL, USERNAME, PASSWORD]):
    print("Error: Missing required environment variables (WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD)")
    sys.exit(1)

BASE_SITE_URL = WP_SITE_URL.rstrip('/') + '/'
WP_API_URL = urljoin(BASE_SITE_URL, 'wp-json/')
auth = (USERNAME, PASSWORD)
headers = {'Content-Type': 'application/json'}
REQUEST_TIMEOUT = 30

def log(msg):
    print(f"[*] {msg}")

def build_url(base, path):
    """Safely join a base URL with a path segment."""
    return urljoin(base.rstrip('/') + '/', path.lstrip('/'))

def update_plugins():
    log("Checking for plugins that need updates...")
    plugins = []
    page = 1
    try:
        while True:
            resp = requests.get(
                build_url(WP_API_URL, '/wp/v2/plugins'),
                params={'per_page': 100, 'page': page},
                auth=auth,
                timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            plugins.extend(resp.json())
            total_pages = int(resp.headers.get('X-WP-TotalPages', '1'))
            if page >= total_pages:
                break
            page += 1
    except RequestException as e:
        log(f"Failed to fetch plugins: {e}")
        return

    if not plugins:
        log("No plugins found from API response.")
        return

    for p in plugins:
        if p.get('status') == 'active' and p.get('_links', {}).get('wp:action-update'):
            log(f"Plugin {p['name']} has an update available.")
            update_link = p['_links']['wp:action-update'][0]['href']
            try:
                update_resp = requests.post(update_link, auth=auth, timeout=REQUEST_TIMEOUT)
                if update_resp.status_code == 200:
                    log(f"  - Successfully updated {p['name']}")
                else:
                    log(f"  - Failed to update {p['name']}: {update_resp.text}")
            except RequestException as e:
                log(f"  - Error updating {p['name']}: {e}")

def audit_rankmath():
    log("Fetching RankMath inspection results to find indexing issues...")
    # This endpoint was verified to exist via manual exploration earlier.
    try:
        resp = requests.get(
            build_url(WP_API_URL, '/rankmath/v1/an/inspectionResults'),
            auth=auth,
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
    except RequestException as e:
        log(f"Failed to fetch RankMath inspection results: {e}")
        return

    if resp.status_code == 200:
        results = resp.json()
        rows = results.get('rows', [])
        for row in rows:
            if row.get('index_verdict') != 'PASS':
                page = row.get('page')
                issue = row.get('coverage_state')
                log(f"Issue found on {page}: {issue}")
                if page:
                    # Format URL properly
                    if not page.startswith('http'):
                        url_to_submit = build_url(BASE_SITE_URL, page)
                    else:
                        url_to_submit = page

                    try:
                        submit_resp = requests.post(
                            build_url(WP_API_URL, '/rankmath/v1/in/submitUrls'),
                            headers=headers,
                            json={"urls": url_to_submit},
                            auth=auth,
                            timeout=REQUEST_TIMEOUT
                        )
                        if submit_resp.status_code == 200:
                            log(f"  - Submitted URL {url_to_submit} to IndexNow/RankMath Indexing.")
                        else:
                            log(f"  - Failed to submit URL via RankMath: {submit_resp.text}")
                    except RequestException as e:
                        log(f"  - Failed to submit URL via RankMath: {e}")
    else:
        log("Failed to fetch RankMath inspection results.")

def audit_sitekit():
    log("Checking Google Site Kit for SEO/health issues...")
    # This endpoint was verified to exist.
    try:
        resp = requests.get(
            build_url(WP_API_URL, '/google-site-kit/v1/core/site/data/health-checks'),
            auth=auth,
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
    except RequestException as e:
        log(f"Failed to fetch Site Kit health checks or plugin not fully configured: {e}")
        return

    if resp.status_code == 200:
        health_data = resp.json()
        checks = health_data.get('checks') if isinstance(health_data, dict) else None
        if isinstance(checks, list):
            status_counts = {}
            for check in checks:
                status = check.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            log(f"Site Kit Health Checks summary: total={len(checks)}, statuses={status_counts}")
        else:
            item_count = len(health_data) if hasattr(health_data, '__len__') else 'unknown'
            log(f"Site Kit Health Checks fetched successfully (items={item_count}).")
    else:
        log("Failed to fetch Site Kit health checks or plugin not fully configured.")

def run_seo_audit():
    log("Running daily SEO audit and applying fixes from discoverers...")
    update_plugins()
    audit_rankmath()
    audit_sitekit()

if __name__ == '__main__':
    log("Starting automated SEO Manager...")
    run_seo_audit()
    log("SEO Manager completed.")
