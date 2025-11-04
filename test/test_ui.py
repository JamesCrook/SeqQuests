from playwright.sync_api import sync_playwright
import time

def run_test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Wait for the server to start
        time.sleep(5)

        page.goto("http://localhost:8000")

        # Click the "Add Job" button to go to the job selection page
        page.click("text=Add Job")
        page.wait_for_load_state()

        # Click the "Data Munging" button to create a new job
        page.click("text=Data Munging")
        page.wait_for_load_state()

        # Select the newly created job
        page.wait_for_selector(".job-item")
        page.click(".job-item")
        page.wait_for_timeout(1000)

        # Click the "Configure" button to open the configuration modal
        page.click("#configureButton")

        # Check the "Mouse" checkbox in the iframe
        iframe = page.frame_locator("#config-iframe")
        iframe.locator("input[value='mouse']").check()

        # Click the "Save Configuration" button
        iframe.locator("text=Save Configuration").click()

        # Start the job
        page.click("#startButton")

        # Re-open the configuration/monitoring modal
        page.click("#configureButton")

        # Wait for the job to make some progress
        page.wait_for_timeout(5000)

        # Check that the progress indicators are updating
        sequences_examined = iframe.locator("#sequences-examined").inner_text()
        proteins_processed = iframe.locator("#proteins-processed").inner_text()

        print(f"Sequences Examined: {sequences_examined}")
        print(f"Proteins Processed: {proteins_processed}")

        if int(sequences_examined) > 0 and int(proteins_processed) > 0:
            print("Test passed!")
        else:
            print("Test failed!")

        browser.close()

run_test()
