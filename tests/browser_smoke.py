"""Headless browser acceptance: Streamlit navigation, interaction, actual downloads."""
import csv
import io
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader


BASE = os.environ.get("FRAGILITY_BASE_URL", "http://127.0.0.1:8765")


def check_responsive(page):
    """Smoke-test both pages at desktop, tablet and narrow mobile widths."""
    for width, height in ((1366, 900), (768, 1024), (390, 844)):
        page.set_viewport_size({"width": width, "height": height})
        expect(page.get_by_role("heading", name="Research Lab", exact=True)).to_be_visible()
        shock = page.get_by_role("spinbutton", name="equities shock (%)")
        shock.scroll_into_view_if_needed()
        expect(shock).to_be_visible()
        shock.focus()
        expect(shock).to_be_focused()
        shock.press("Tab")
        expect(shock).not_to_be_focused()
        expect(page.get_by_role("button", name="Download PDF", exact=True)).to_be_enabled()
        assert not page.locator("[data-testid='stException']").count()
        print(f"Research Lab viewport and keyboard smoke: {width}x{height}", flush=True)

    page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
    for width, height in ((390, 844), (768, 1024), (1366, 900)):
        page.set_viewport_size({"width": width, "height": height})
        expect(page.get_by_role("heading", name="Fragility Atlas", exact=True)).to_be_visible(timeout=60000)
        tab = page.get_by_role("tab", name="Scenario Explorer", exact=True)
        tab.focus()
        expect(tab).to_be_focused()
        tab.press("Enter")
        expect(tab).to_have_attribute("aria-selected", "true")
        expect(page.get_by_role("heading", name="Scenario Explorer", exact=True)).to_be_visible()
        assert not page.locator("[data-testid='stException']").count()
        print(f"Dashboard viewport and keyboard smoke: {width}x{height}", flush=True)


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(accept_downloads=True, viewport={"width": 1366, "height": 900})
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
            expect(page.get_by_role("heading", name="Fragility Atlas", exact=True)).to_be_visible(timeout=60000)
            expect(page.get_by_text("QUANTITATIVE RISK RESEARCH / SCENARIO INTELLIGENCE", exact=True)).to_be_visible()

            # Navigate via the Streamlit multipage sidebar rather than assuming URL routing.
            page.get_by_role("link", name="Research Lab").click(timeout=30000)
            expect(page.get_by_role("heading", name="Research Lab", exact=True)).to_be_visible(timeout=60000)
            pnl = page.get_by_text("Linear scenario P&L (USD)", exact=True)
            expect(pnl).to_be_visible()

            # Changing a factor shock should rerun the page without an exception.
            shock = page.get_by_role("spinbutton", name="equities shock (%)")
            shock.fill("-10")
            shock.press("Tab")
            # Wait for the new numerical result and the completed rerun, not the unchanged heading.
            expect(page.get_by_text("$-52,200.00", exact=True)).to_be_visible(timeout=60000)
            expect(page.get_by_test_id("stStatusWidget")).to_be_hidden(timeout=60000)

            for label, extension in (
                ("Download JSON", ".json"),
                ("Download CSV", ".csv"),
                ("Download PDF", ".pdf"),
            ):
                expect(page.get_by_role("button", name=label, exact=True)).to_be_enabled(timeout=60000)
                expect(page.get_by_test_id("stStatusWidget")).to_be_hidden(timeout=60000)
                with page.expect_download(timeout=60000) as download_info:
                    page.get_by_role("button", name=label, exact=True).click()
                download = download_info.value
                failure = download.failure()
                assert failure is None, f"{label} failed: {failure}"
                data = Path(download.path()).read_bytes()
                assert data, f"Empty {extension} download"
                if extension == ".json":
                    report = json.loads(data.decode("utf-8"))
                    assert "portfolio_input_sha256" in report["metadata"]
                    assert "expected_shortfall" in report["historical"]
                    assert report["stress"]["pnl"] == -52200.0
                elif extension == ".csv":
                    rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
                    assert any(row[0] == "metadata.portfolio_input_sha256" for row in rows)
                    assert any(row[0] == "historical.expected_shortfall" for row in rows)
                else:
                    assert data.startswith(b"%PDF")
                    pdf = PdfReader(io.BytesIO(data))
                    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                    assert "Fragility Atlas" in text
                    assert "historical.expected_shortfall" in text
                    assert "Executive summary" in text
            assert not page.locator("[data-testid='stException']").count()
            check_responsive(page)
        finally:
            page.screenshot(path="/tmp/fragility-browser-smoke.png", full_page=True)
            browser.close()


if __name__ == "__main__":
    main()
