import requests
import json
import os
import sys

WP_SITE_URL = os.getenv('WP_SITE_URL')
USERNAME = os.getenv('WP_USERNAME')
PASSWORD = os.getenv('WP_APP_PASSWORD')

if not all([WP_SITE_URL, USERNAME, PASSWORD]):
    print("Error: Missing required environment variables (WP_SITE_URL, WP_USERNAME, WP_APP_PASSWORD)")
    sys.exit(1)

WP_API_URL = WP_SITE_URL + '/wp-json'
auth = (USERNAME, PASSWORD)
headers = {'Content-Type': 'application/json'}

def log(msg):
    print(f"[*] {msg}")

def update_plugins():
    log("Checking for plugins that need updates...")
    resp = requests.get(f"{WP_API_URL}/wp/v2/plugins", auth=auth)
    if resp.status_code == 200:
        plugins = resp.json()
        for p in plugins:
            if p.get('status') == 'active' and p.get('_links', {}).get('wp:action-update'):
                log(f"Plugin {p['name']} has an update available.")
                update_link = p['_links']['wp:action-update'][0]['href']
                try:
                    update_resp = requests.post(update_link, auth=auth)
                    if update_resp.status_code == 200:
                        log(f"  - Successfully updated {p['name']}")
                    else:
                        log(f"  - Failed to update {p['name']}: {update_resp.text}")
                except Exception as e:
                    log(f"  - Error updating {p['name']}: {e}")
    else:
        log("Failed to fetch plugins.")

def audit_rankmath():
    log("Fetching RankMath inspection results to find indexing issues...")
    # This endpoint was verified to exist via manual exploration earlier.
    resp = requests.get(f"{WP_API_URL}/rankmath/v1/an/inspectionResults", auth=auth)
    if resp.status_code == 200:
        results = resp.json()
        rows = results.get('rows', [])
        for row in rows:
            if row.get('index_verdict') != 'PASS':
                page = row.get('page')
                obj_id = row.get('object_id')
                issue = row.get('coverage_state')
                log(f"Issue found on {page}: {issue}")
                if obj_id:
                    # Format URL properly
                    if not page.startswith('http'):
                        url_to_submit = f"{WP_SITE_URL}{page}"
                    else:
                        url_to_submit = page

                    submit_resp = requests.post(
                        f"{WP_API_URL}/rankmath/v1/in/submitUrls",
                        headers=headers,
                        json={"urls": url_to_submit},
                        auth=auth
                    )
                    if submit_resp.status_code == 200:
                        log(f"  - Submitted URL {url_to_submit} to IndexNow/RankMath Indexing.")
                    else:
                        log(f"  - Failed to submit URL via RankMath: {submit_resp.text}")
    else:
        log("Failed to fetch RankMath inspection results.")

def audit_sitekit():
    log("Checking Google Site Kit for SEO/health issues...")
    # This endpoint was verified to exist.
    resp = requests.get(f"{WP_API_URL}/google-site-kit/v1/core/site/data/health-checks", auth=auth)
    if resp.status_code == 200:
        health_data = resp.json()
        log(f"Site Kit Health Checks: {health_data}")
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
