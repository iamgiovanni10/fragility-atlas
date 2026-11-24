"""Headless browser acceptance: Streamlit navigation, interaction, actual downloads."""
import csv
import io
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright, expect
from pypdf import PdfReader


BASE = os.environ.get("FRAGILITY_BASE_URL", "http://127.0.0.1:8765")


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(accept_downloads=True, viewport={"width": 1366, "height": 900})
        try:
            page.goto(BASE, wait_until="domcontentloaded", timeout=60000)
            expect(page.get_by_role("heading", name="Fragility Atlas", exact=True)).to_be_visible(timeout=60000)
            expect(page.get_by_text("Scenario Intelligence v0.3", exact=False).first).to_be_visible()

            # Navigate via the Streamlit multipage sidebar rather than assuming URL routing.
            page.get_by_role("link", name="Research Lab").click(timeout=30000)
            expect(page.get_by_role("heading", name="Research Lab", exact=True)).to_be_visible(timeout=60000)
            pnl = page.get_by_text("Linear scenario P&L (USD)", exact=True)
            expect(pnl).to_be_visible()

            # Changing a factor shock should rerun the page without an exception.
            shock = page.get_by_role("spinbutton", name="equities shock (%)")
            shock.fill("-10")
            shock.press("Tab")
            expect(page.get_by_role("heading", name="Research Lab", exact=True)).to_be_visible(timeout=60000)

            for label, extension in (
                ("Download JSON", ".json"),
                ("Download CSV", ".csv"),
                ("Download PDF", ".pdf"),
            ):
                with page.expect_download(timeout=60000) as download_info:
                    page.get_by_role("button", name=label, exact=True).click()
                download = download_info.value
                data = Path(download.path()).read_bytes()
                assert data, f"Empty {extension} download"
                if extension == ".json":
                    report = json.loads(data.decode("utf-8"))
                    assert "portfolio_input_sha256" in report["metadata"]
                    assert "expected_shortfall" in report["historical"]
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
            assert not page.locator("[data-testid='stException']").count()
        finally:
            page.screenshot(path="/tmp/fragility-browser-smoke.png", full_page=True)
            browser.close()


if __name__ == "__main__":
    main()
