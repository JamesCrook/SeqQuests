# py/make_doc_images.py
#
# Python scripts are run from the top level directory with it as the working directory.

import os
import time
import argparse
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright
from functools import partial


# List of pages that have help.js and a hamburger menu
PAGES = [
    'static/bias_analysis.html',
    'static/domain-viewer.html',
    'static/fast-align.html',
    'static/fetch-seq.html',
    'static/match_explorer.html',
]

def run_server(port, directory):
    # Create a handler that is fixed to the specific directory 
    # without changing the process's working directory.
    handler = partial(SimpleHTTPRequestHandler, directory=directory)
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    print(f"Serving files from '{directory}' at http://localhost:{port}")
    httpd.serve_forever()

def capture_help_images(browser, page_url, output_dir, width, height, organizer_pos):
    context = browser.new_context(viewport={'width': width, 'height': height})
    page = context.new_page()

    # Open the page
    full_url = f"http://localhost:8000/{page_url}"
    print(f"Opening {full_url}")
    try:
        page.goto(full_url, timeout=30000)
    except Exception as e:
        print(f"Failed to load {page_url}: {e}")
        context.close()
        return

    # Wait for rendering
    page.wait_for_timeout(200)

    # Click the hamburger menu
    print("Clicking hamburger menu")
    try:
        page.wait_for_selector('#hamburger-menu', state='visible', timeout=5000)
        page.click('#hamburger-menu')
        page.wait_for_timeout(100)

        # Click Help
        print("Clicking Help")
        # We scope it to the dropdown to ensure we don't click a 'Help' button in the footer or header
        page.locator('.hamburger-dropdown').get_by_text("Help", exact=True).click()
        page.wait_for_timeout(100)
    except Exception as e:
        print(f"Menu interaction failed on {page_url}: {e}")

    # Verify help organizer presence and visibility
    # If menu click failed or didn't trigger, try forcing DoHelp()
    try:
        if not page.locator('.help-organizer').is_visible():
            print("Help organizer not visible, attempting to force DoHelp()")
            page.evaluate("if (typeof window.DoHelp === 'function') window.DoHelp();")
            page.wait_for_timeout(100)

        page.wait_for_selector('.help-organizer', state='visible', timeout=5000)
    except Exception as e:
        print(f"Failed to activate help on {page_url}: {e}")
        context.close()
        return

    # Move help organizer if requested
    if organizer_pos == 'bottom-right':
        page.evaluate("""
            const el = document.querySelector('.help-organizer');
            if (el) {
                el.style.top = 'auto';
                el.style.left = 'auto';
                el.style.bottom = '20px';
                el.style.right = '20px';
                el.style.transform = 'none';
            }
        """)
        page.wait_for_timeout(500)

    # Capture first screenshot
    base_name = os.path.basename(page_url).replace('.html', '')
    img_path = os.path.join(output_dir, f"{base_name}_help_1.png")
    print(f"Capturing {img_path}")
    page.screenshot(path=img_path)

    # Check for "Next" button
    next_btn = page.locator('.help-btn-next')

    try:
        if next_btn.is_visible():
            print("Next button found. Clicking Next.")
            next_btn.click()
            page.wait_for_timeout(100)

            img_path_2 = os.path.join(output_dir, f"{base_name}_help_2.png")
            print(f"Capturing {img_path_2}")
            page.screenshot(path=img_path_2)
    except Exception as e:
        print(f"Error handling Next button on {page_url}: {e}")

    context.close()

def main():
    parser = argparse.ArgumentParser(description='Capture documentation images.')
    parser.add_argument('--width', type=int, default=1280, help='Browser width')
    parser.add_argument('--height', type=int, default=800, help='Browser height')
    parser.add_argument('--organizer-pos', type=str, default=None, choices=['bottom-right'], help='Position of help organizer')
    parser.add_argument('--output', type=str, default='docs/images', help='Output directory')
    parser.add_argument('--port', type=int, default=8000, help='Port for local server')
    parser.add_argument('--serve-dir', type=str, default='.', help='Directory to serve')
    args = parser.parse_args()

    # Start the server in a background thread
    server_thread = threading.Thread(
        target=run_server, 
        args=(args.port, args.serve_dir),
        daemon=True  # 'daemon=True' ensures the thread dies when the main script ends
    )
    server_thread.start()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        for page_url in PAGES:
            capture_help_images(browser, page_url, args.output, args.width, args.height, args.organizer_pos)
        browser.close()

if __name__ == '__main__':
    main()
