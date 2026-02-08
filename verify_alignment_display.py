
from playwright.sync_api import sync_playwright
import os
import time

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate to the page
    # Using localhost:8000 assuming python server is running from repo root
    page.goto("http://localhost:8000/static/match_explorer.html")

    # Wait for formatAlignment to be available (from sw_support.js)
    # Just in case, wait for load
    page.wait_for_load_state("networkidle")

    # Inject mock data and format function execution
    page.evaluate("""
        const alignmentViewer = document.getElementById('alignmentViewer');
        if (alignmentViewer) {
            // Define test data
            const testAlignments = [
                {
                    name: "Short Sequence",
                    align1: "ABCDE",
                    align2: "AB-DE",
                    matches: "|| ||",
                    seq1_start: 9,
                    seq2_start: 19
                },
                {
                    name: "Full Sequence (70 chars)",
                    align1: "A".repeat(70),
                    align2: "B".repeat(70),
                    matches: "|".repeat(70),
                    seq1_start: 99,
                    seq2_start: 199
                },
                {
                    name: "Overflow Sequence (75 chars)",
                    align1: "A".repeat(75),
                    align2: "B".repeat(75),
                    matches: "|".repeat(75),
                    seq1_start: 99,
                    seq2_start: 199
                }
            ];

            let htmlContent = '';

            testAlignments.forEach(align => {
                htmlContent += `<div style="font-weight:bold; margin-top: 20px;">${align.name}</div>`;
                const lines = formatAlignment(align);
                htmlContent += lines.join('\\n');
            });

            alignmentViewer.innerHTML = htmlContent;

            // Adjust styles for better screenshot visibility
            alignmentViewer.style.height = 'auto';
            alignmentViewer.style.overflow = 'visible';
            const pairViewer = document.getElementById('pairViewer');
            if (pairViewer) {
                pairViewer.style.height = 'auto';
                pairViewer.style.overflow = 'visible';
            }
            document.body.style.height = 'auto';
            document.body.style.overflow = 'visible';
        } else {
            console.error("Alignment viewer not found");
        }
    """)

    if not os.path.exists("verification"):
        os.makedirs("verification")

    # Take screenshot
    page.screenshot(path="verification/alignment_verification.png", full_page=True)
    browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
