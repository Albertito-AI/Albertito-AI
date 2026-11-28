"""Play fixed match positions in a served arcade or an extracted Maths_Arcade.html.

Use the repository's Playwright environment, then run
python scripts/math_arcade/check_matches.py https://albertito-ai.github.io/Albertito-AI/math-arcade/
A file:/// URL checks the portable edition with the browser offline.
"""
import argparse
import re
from urllib.parse import urlsplit

from playwright.sync_api import expect, sync_playwright


def check(browser, base):
    origin = urlsplit(base)
    context = browser.new_context(offline=origin.scheme == "file", viewport={"width": 390, "height": 844})
    failures = []

    def allow_local(route):
        asset = urlsplit(route.request.url)
        if asset.scheme in ("http", "https") and (asset.scheme, asset.netloc) != (origin.scheme, origin.netloc):
            failures.append(route.request.url)
            route.abort()
        else:
            route.continue_()

    context.route("**/*", allow_local)
    page = context.new_page()
    page.on("pageerror", lambda error: failures.append(str(error)))
    board = page.locator("#match-board")
    result = page.locator("#match-summary")

    def move(name):
        board.get_by_role("button", name=name, exact=True).click()

    page.goto(base + "#match")
    expect(page.locator("#match-game option")).to_have_count(6)
    expect(page.locator("#match-strength input")).to_have_count(3)
    page.goto(base + "#match/lattice/0/2")
    for name in ["Jump 1: x −1, y +1", "Jump 4: x +1, y 0", "Jump 1: x −1, y +1"]:
        move(name)
    expect(result).to_contain_text("You finished in 3 jumps")
    page.goto(base + "#match/parity/0/7")
    move("A1, lit")
    move("C3, lit")
    expect(result).to_contain_text("You finished in 2 presses")
    page.goto(base + "#match/forge/2/0")
    for name in ["Tile 3, value 8", "Divide", "Tile 1, value 7", "Tile 2, value 9",
                 "Subtract", "Tile 3, value 8/7", "Tile 1, value 7", "Multiply",
                 "Tile 2, value 55/7", "Submit expression"]:
        move(name)
    expect(result).to_contain_text("You made 55 (distance 0")
    page.goto(base + "#match/sudoku/0/0")
    expect(board.get_by_role("button", name="Full board")).to_have_attribute("aria-pressed", "true")
    board.get_by_role("button", name=re.compile("Short checkpoint")).click()
    # Pass five rival placements to verify a completed loss and the terminal view.
    for _ in range(10):
        move("Pass a turn")
    expect(result).to_contain_text("The rival reached the checkpoint first")
    page.goto(base + "#match/nim/1/7")
    move("Let Atlas move first")
    expect(board.get_by_role("status")).to_contain_text("Atlas took")
    page.goto(base + "#match/reversi/1/7")
    board.get_by_role("button", name=re.compile(", legal move$")).first.click()
    expect(board.get_by_role("button", name=re.compile(", legal move$")).first).to_be_enabled()
    assert not failures, failures
    context.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--browser-executable")
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.browser_executable)
        try:
            check(browser, args.url)
        finally:
            browser.close()
    print("Six match routes passed.")
