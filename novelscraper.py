import os, time, sys, textwrap, json, requests, random, zipfile, platform, subprocess, re, html, glob
from colorama import Back, Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
try:
    import fade
except ImportError:
    os.system("pip install fade==0.0.9")
    import fade
try:
    from ebooklib import epub # type: ignore
except ImportError:
    os.system("pip install EbookLib")
    from ebooklib import epub # type: ignore
try:
    import colorama
except ImportError:
    os.system("pip install colorama==0.4.6")
    import colorama
try:
    import selenium
except ImportError:
    os.system("pip install selenium==4.35.0")
    import selenium
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    os.system("pip install webdriver-manager")
    from webdriver_manager.chrome import ChromeDriverManager
try:
    import undetected_chromedriver as uc
except ImportError:
    os.system("pip install undetected-chromedriver")
    import undetected_chromedriver as uc

chrome_browser_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_driver_path = "NONE"
VERSION = "2.5"

# ── Default settings (overridden by config.json if present) ──────────────
SETTINGS = {
    "download_format": "txt",       # "txt" or "epub"
    "translate":       False,       # auto-translate Korean → English
    "theme":           "purplepink" # fade colour theme for ASCII art
}

# All valid fade colour methods (single-argument string → text)
FADE_THEMES = [
    "purplepink", "pinkred", "greenblue", "fire", "water",
    "ocean", "lime", "brazil", "russia", "random",
    "purpleblue", "blackwhite", "gold", "metal", "earth",
]

def _apply_fade(text: str) -> str:
    """Apply the current theme from SETTINGS to text via fade."""
    theme = SETTINGS.get("theme", "purplepink")
    if theme == "ocean":
        return fade.water(text)          # fade.ocean doesn't exist; water is the closest
    func = getattr(fade, theme, None)
    if func is None:
        func = fade.purplepink
    return func(text)

# Each theme's two endpoint colours: (primary/bracket, secondary/text)
_THEME_COLOURS = {
    "purplepink":  (Fore.MAGENTA,        Fore.LIGHTMAGENTA_EX),
    "pinkred":     (Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX),
    "greenblue":   (Fore.GREEN,           Fore.LIGHTCYAN_EX),
    "fire":        (Fore.RED,             Fore.LIGHTYELLOW_EX),
    "water":       (Fore.BLUE,            Fore.LIGHTCYAN_EX),
    "ocean":       (Fore.BLUE,            Fore.CYAN),
    "lime":        (Fore.GREEN,           Fore.LIGHTGREEN_EX),
    "brazil":      (Fore.GREEN,           Fore.YELLOW),
    "russia":      (Fore.RED,             Fore.WHITE),
    "purpleblue":  (Fore.MAGENTA,         Fore.BLUE),
    "blackwhite":  (Fore.WHITE,           Fore.LIGHTBLACK_EX),
    "gold":        (Fore.YELLOW,          Fore.WHITE),
    "metal":       (Fore.LIGHTBLUE_EX,    Fore.WHITE),
    "earth":       (Fore.YELLOW,          Fore.GREEN),
}

_RANDOM_COLOURS = [
    Fore.MAGENTA, Fore.LIGHTMAGENTA_EX, Fore.LIGHTRED_EX, Fore.RED,
    Fore.LIGHTCYAN_EX, Fore.CYAN, Fore.BLUE, Fore.LIGHTBLUE_EX,
    Fore.GREEN, Fore.LIGHTGREEN_EX, Fore.YELLOW, Fore.LIGHTYELLOW_EX,
    Fore.WHITE,
]

def T() -> str:
    """Primary colour for the current theme (brackets, borders)."""
    if SETTINGS.get("theme") == "random":
        return random.choice(_RANDOM_COLOURS)
    return _THEME_COLOURS.get(SETTINGS.get("theme", "purplepink"), (Fore.MAGENTA, Fore.LIGHTMAGENTA_EX))[0]

def T2() -> str:
    """Secondary colour for the current theme (inner text, separators)."""
    if SETTINGS.get("theme") == "random":
        return random.choice(_RANDOM_COLOURS)
    return _THEME_COLOURS.get(SETTINGS.get("theme", "purplepink"), (Fore.MAGENTA, Fore.LIGHTMAGENTA_EX))[1]

def load_config():
    global chrome_driver_path, SETTINGS
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            chrome_driver_path = config.get("DRIVERPATH", "NONE")
            for key in SETTINGS:
                if key in config:
                    SETTINGS[key] = config[key]
        except json.JSONDecodeError as e:
            print(f"Error reading config.json: {e}")

def save_config():
    try:
        config = {}
        if os.path.exists('config.json'):
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
            except json.JSONDecodeError:
                config = {}
        config["DRIVERPATH"] = chrome_driver_path
        for key, val in SETTINGS.items():
            config[key] = val
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

load_config()

w = Fore.WHITE
b = Fore.BLACK
g = Fore.LIGHTGREEN_EX
ly = Fore.LIGHTYELLOW_EX
lm = Fore.LIGHTMAGENTA_EX
c = Fore.LIGHTCYAN_EX
lr = Fore.LIGHTRED_EX
lb = Fore.LIGHTBLUE_EX
m = Fore.MAGENTA
bb = Fore.BLUE
rr = Fore.RESET
r = Fore.RED
y = Fore.YELLOW
gg = Fore.GREEN

random_loading_medium = random.uniform(0.7, 1.5)
random_loading_small = random.uniform(0.4, 0.9)
random_loading_large = random.uniform(1.2, 2.1)

def Spinner():
    l = ['|', '/', '-', '\\', ' ']
    for i in l+l+l:
        sys.stdout.write(f"""\r {i}""")
        sys.stdout.flush()
        time.sleep(0.1)

def press_any_key():
    try:
        import msvcrt
        print(f"\n{T()}[{T2()}#{T()}] {w}Press any key to continue...", end="", flush=True)
        msvcrt.getch()
    except ImportError:
        import sys, tty, termios
        print(f"\n{T()}[{T2()}#{T()}] {w}Press any key to continue...", end="", flush=True)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def save_to_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def save_as_epub(folder_path, novel_title):
    from ebooklib import epub

    def safe_filename(name):
        return re.sub(r'[\\/*?:"<>|]', '-', name).strip()

    def extract_chapter_number(name):
        m = re.search(r'(?:chapter|episode)[^0-9]*?(\d+(?:\.\d+)?)', name, flags=re.IGNORECASE)
        if m:
            num = m.group(1)
            try:
                return int(num) if '.' not in num else float(num)
            except:
                return float('inf')
        m2 = re.search(r'(\d+(?:\.\d+)?)', name)
        if m2:
            num = m2.group(1)
            try:
                return int(num) if '.' not in num else float(num)
            except:
                return float('inf')
        return float('inf')

    def natural_key(s):
        parts = re.split(r'(\d+)', s.lower())
        return [int(p) if p.isdigit() else p for p in parts]

    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        print(f"{Fore.RED}[{Fore.WHITE}X{Fore.RED}]{w} No .txt files found to convert.")
        return

    files_with_nums = []
    for p in txt_files:
        base = os.path.basename(p)
        num = extract_chapter_number(base)
        files_with_nums.append((num, base, p))

    files_with_nums.sort(key=lambda x: (x[0], natural_key(x[1])))
    sorted_files = [item[2] for item in files_with_nums]

    book = epub.EpubBook()
    book.set_identifier(safe_filename(novel_title.lower()) or "novel")
    book.set_title(novel_title)
    book.set_language("en")
    book.add_author("TopStop5's Novelscraper")
    try:
        book.add_metadata('DC', 'creator', 'Novelscraper by TopStop5')
        book.add_metadata('DC', 'title', novel_title)
    except Exception:
        pass

    chapters = []
    total_chaps = len(sorted_files)
    zero_pad = len(str(total_chaps))

    for idx, file_path in enumerate(sorted_files, 1):
        fname = os.path.basename(file_path)
        chap_title = os.path.splitext(fname)[0]
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        paras = [p.strip() for p in re.split(r'(?:\r?\n){2,}', text) if p.strip()]
        html_body = ''.join(f'<p>{html.escape(p)}</p>' for p in paras)
        html_doc = f'<?xml version="1.0" encoding="utf-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{html.escape(chap_title)}</title></head><body>{html_body}</body></html>'

        ch = epub.EpubHtml(title=chap_title, file_name=f'chapter_{str(idx).zfill(zero_pad)}.xhtml', lang='en')
        ch.content = html_doc
        book.add_item(ch)
        chapters.append(ch)

    book.toc = chapters
    book.spine = ['nav'] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    output_path = os.path.join(folder_path, f"{safe_filename(novel_title)}.epub")
    epub.write_epub(output_path, book)
    print(f"\n{g}[{w}!{g}]{w} EPUB created: {output_path}")


# ─────────────────────────────────────────────
#  SBXH2 HANDLER
# ─────────────────────────────────────────────

translate_cache: dict = {}

def translate_text(text: str) -> str:
    if not text or not text.strip():
        return text
    if text in translate_cache:
        return translate_cache[text]
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=ko&tl=en&dt=t&q={requests.utils.quote(text)}"
        )
        resp = requests.get(url, timeout=10)
        data = resp.json()
        result = "".join(t[0] for t in data[0] if t[0])
        translate_cache[text] = result
        return result
    except Exception:
        return text


def translate_lines(lines: list) -> list:
    chunk_size = 25
    out = list(lines)
    for i in range(0, len(out), chunk_size):
        chunk = out[i : i + chunk_size]
        out[i : i + chunk_size] = [translate_text(l) for l in chunk]
    return out


def clean_sbxh2_chapter_text(raw: str):
    """
    Strip site chrome from clipboard/innerText on sbxh2/newtokki pages.

    Strategy
    --------
    The breadcrumb line always looks like (Korean or English):
        홈 › 소설 › <title> › N화
        home › novel › <title> › Episode N
    Everything BEFORE and INCLUDING that line is site header chrome.

    After the breadcrumb the actual chapter content follows, but it ends
    with a navigation footer that always starts with one of:
        ‹ Previous episode   /   ‹ 이전화
    followed by nav links and a font-size control block
        letter−16px+basic
    Everything from that footer onward is stripped too.
    """
    if not raw:
        return None

    text = raw.replace("\r", "")

    # ── 1. Trim header ──────────────────────────────────────────────
    # The page structure is always:
    #   ... site chrome ...
    #   홈 › 소설 › <title> › N화 <chapter-title>   ← breadcrumb
    #   ‹ 이전화  목록  책갈피  다음화 ›              ← nav bar
    #   글자 − 16px + 기본                           ← font-size control
    #   <actual story content starts here>
    #
    # Strategy: find the font-size control line and start content AFTER it.
    # If that line is absent, fall back to cutting after the breadcrumb.

    # Primary: cut after the font-size control line (글자 − NNpx  OR  letter − NNpx)
    font_ctrl_pattern = re.compile(
        r"(?:글자|letter)\s*[-−]\s*\d+px[^\n]*",
        re.IGNORECASE,
    )
    fm = font_ctrl_pattern.search(text)
    if fm:
        text = text[fm.end():]
    else:
        # Fallback: cut after the breadcrumb line (everything up to end of that line)
        breadcrumb_pattern = re.compile(
            r"(?:홈|home)\s*[›>]\s*(?:소설|novel)\s*[›>][^\n]*",
            re.IGNORECASE,
        )
        bm = breadcrumb_pattern.search(text)
        if bm:
            text = text[bm.end():]
        else:
            # Last resort: strip known site-chrome blocks line by line
            noise_lines = re.compile(
                r"^\s*(?:"
                r"https?://\S+|"
                r"@\w+|"
                r"[🐰🌙🏆🔧📢🛠️].*|"
                r"(?:New Rabbit|Newtokki|뉴토끼).*|"
                r"(?:home|홈|webtoon|웹툰|novel|소설|comic book|만화|"
                r"animated film|애니|ranking|랭킹|game|게임|"
                r"community|커뮤니티|bookmark|북마크|event|이벤트|"
                r"patch notes?|패치노트|announcement|공지사항|"
                r"log\s*in|로그인|join the membership|회원가입|"
                r"customer service center|고객센터|"
                r"download the app|앱 다운로드|telegram channel|텔레그램 채널|"
                r"search by work|recently viewed works|최근본작품|"
                r"point ranking|포인트랭킹|advertising inquiry|광고문의|"
                r"this feature is in preparation|준비 중|"
                r"basic|dark)\s*"
                r")\s*$",
                re.IGNORECASE,
            )
            text = "\n".join(
                line for line in text.splitlines()
                if not noise_lines.match(line)
            )

    # ── 2. Trim footer ──────────────────────────────────────────────
    footer_pattern = re.compile(
        r"(?:‹\s*(?:Previous episode|이전화)|"
        r"(?:letter|글자)\s*[-−]\s*\d+px|"   # English "letter−16px" OR Korean "글자 − 16px"
        r"inventory|북마크|bookmark)"
        r".*",
        re.IGNORECASE | re.DOTALL,
    )
    text = footer_pattern.sub("", text)

    # ── 3. General noise passes ─────────────────────────────────────
    misc_patterns = [
        r"^https?://\S+$",
        r"@\w+\s*",
        r"^basic\s*$",
        r"^dark\s*$",
        # NOTE: do NOT add generic words like "awakening" here — they are common
        # story vocabulary (e.g. 각성 = awakening) and will wipe out real content.
    ]
    for p in misc_patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE | re.MULTILINE)

    # ── 4. Normalise whitespace ─────────────────────────────────────
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return text if text else None


def _is_cloudflare_challenge(driver) -> bool:
    """
    Return True if the current page is a Cloudflare challenge/verification screen
    that requires manual user interaction (i.e. uc could NOT auto-solve it).
    Detects both the JS-challenge title and the "Performing security verification"
    body text that appears on the interactive CAPTCHA variant.
    """
    CF_TITLE_FRAGMENTS = [
        "just a moment", "checking your browser", "please wait",
        "security check", "enable javascript", "one moment", "attention required",
    ]
    CF_BODY_FRAGMENTS = [
        "performing security verification",
        "this website uses a security service",
        "verifies you are not a bot",
        "verify you are human",
        "cf-challenge",
        "challenge-platform",
    ]
    try:
        title = (driver.title or "").lower()
        if any(frag in title for frag in CF_TITLE_FRAGMENTS):
            return True
        if "__cf_chl" in (driver.current_url or ""):
            return True
        body = (driver.execute_script(
            "return document.body ? document.body.innerText : '';"
        ) or "").lower()
        if any(frag in body for frag in CF_BODY_FRAGMENTS):
            return True
    except Exception:
        pass
    return False


def wait_for_cloudflare(driver, timeout: int = 30) -> bool:
    """
    Wait for a Cloudflare challenge to clear.

    * Auto-challenges (JS spinner): uc resolves these on its own; we just poll.
    * Manual CAPTCHA ("Performing security verification"): we PAUSE scraping,
      print a clear notice, and wait up to 5 minutes for the user to solve it
      in the browser window.  Scraping resumes automatically once the page loads.
    """
    manual_notified = False
    manual_deadline = None

    deadline = time.time() + timeout
    while True:
        now = time.time()

        is_cf = _is_cloudflare_challenge(driver)

        if is_cf:
            # Check whether this is the manual-verification variant
            try:
                body = (driver.execute_script(
                    "return document.body ? document.body.innerText : '';"
                ) or "").lower()
                needs_manual = any(frag in body for frag in [
                    "performing security verification",
                    "this website uses a security service",
                    "verifies you are not a bot",
                    "verify you are human",
                ])
            except Exception:
                needs_manual = False

            if needs_manual:
                if not manual_notified:
                    manual_notified = True
                    manual_deadline = time.time() + 300   # 5-minute window
                    print(f"\n{T()}╔══════════════════════════════════════════════════╗")
                    print(f"{T()}║  {Fore.LIGHTRED_EX}⚠  CLOUDFLARE MANUAL VERIFICATION REQUIRED  {Fore.LIGHTRED_EX}⚠  ║")
                    print(f"{T()}╠══════════════════════════════════════════════════╣")
                    print(f"{T()}║  {Fore.WHITE}Scraping has been PAUSED.                       {T()}║")
                    print(f"{T()}║  {Fore.WHITE}Please solve the CAPTCHA in the Chrome window.  {T()}║")
                    print(f"{T()}║  {Fore.WHITE}Scraping will resume automatically afterwards.  {T()}║")
                    print(f"{T()}╚══════════════════════════════════════════════════╝{Fore.RESET}\n")
                # Use the extended 5-min deadline while waiting for manual solve
                if manual_deadline and time.time() > manual_deadline:
                    print(f"{r}[{w}!{r}]{w} Cloudflare timeout — could not verify after 5 minutes.")
                    return False
                time.sleep(2)
                continue
            else:
                # Auto-challenge — just wait out the normal timeout
                if now > deadline:
                    return True  # uc usually handles it; optimistically continue
                time.sleep(1)
                continue

        # No CF challenge detected
        try:
            body_text = driver.execute_script(
                "return document.body ? document.body.innerText : '';"
            ) or ""
            if len(body_text.strip()) > 200:
                if manual_notified:
                    print(f"{g}[{w}!{g}]{w} Cloudflare cleared — resuming scrape …\n")
                return True
        except Exception:
            pass

        if now > deadline:
            return True  # optimistically continue

        time.sleep(1)


def get_chapter_list(driver, novel_index_url: str) -> list:
    """
    Return a list of dicts sorted by episode number:
        {"ep": int, "url": str, "title": str}

    Reads the chapter <a> links directly from the novel index page.
    Chapter IDs in the URL are NOT sequential integers — only the
    scraped URLs are reliable.

    NOTE: the caller must already have navigated to the index page and
    waited for CF to clear before calling this.  We do NOT re-navigate
    here so we don't blow away the already-cleared session.
    """
    print(f"{T()}[{T2()}!{T()}]{w} Reading chapter list from current page …")

    # Wait for at least one chapter-style link to exist in the DOM
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a[href*='/novel/']")
            )
        )
    except TimeoutException:
        pass

    time.sleep(1)   # small settle for lazy-loaded content

    anchors = driver.find_elements(By.CSS_SELECTOR, "a[href*='/novel/']")
    ep_pattern = re.compile(r"(\d+)화")

    chapters = []
    seen_urls = set()

    for a in anchors:
        href = a.get_attribute("href") or ""
        if not href or href in seen_urls:
            continue
        # Must be a chapter URL: exactly 3 path segments /novel/<id>/<chapterId>
        parts = urlparse(href).path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "novel":
            continue
        seen_urls.add(href)

        text = (a.get_attribute("innerText") or a.text or "").strip()
        mp = ep_pattern.search(text)
        if not mp:
            continue
        ep_num = int(mp.group(1))

        lines = [l.strip() for l in text.splitlines() if l.strip()]
        subtitle = lines[1] if len(lines) > 1 else ""

        chapters.append({"ep": ep_num, "url": href, "title": subtitle})

    chapters.sort(key=lambda x: x["ep"])
    return chapters


def extract_via_clipboard(driver):
    """
    Extract visible page text by simulating Ctrl+A / Ctrl+C and reading the
    system clipboard.  This captures content that is visually rendered but
    not reachable via JS innerText (Shadow DOM, protected containers, etc.).
    Falls back to JS innerText if the clipboard approach yields nothing.
    """
    try:
        import pyperclip
    except ImportError:
        import subprocess
        subprocess.call([sys.executable, "-m", "pip", "install", "pyperclip", "--quiet"])
        import pyperclip

    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys

    # ── 1. Clipboard approach ────────────────────────────────────────
    try:
        # Clear clipboard first so we can detect a failed copy
        pyperclip.copy("")
        time.sleep(0.3)

        # Click the body to make sure the page has focus
        driver.execute_script("document.body.click();")
        time.sleep(0.3)

        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
        time.sleep(0.4)
        actions = ActionChains(driver)
        actions.key_down(Keys.CONTROL).send_keys("c").key_up(Keys.CONTROL).perform()
        time.sleep(0.5)

        text = pyperclip.paste()
        if text and len(text.strip()) > 80:
            return text
    except Exception:
        pass

    # ── 2. JS fallback: stripped body clone ─────────────────────────
    try:
        text = driver.execute_script("""
            var clone = document.body.cloneNode(true);
            var junk = clone.querySelectorAll(
                'script,style,nav,header,footer,button,input,select,noscript'
            );
            junk.forEach(function(el){ el.parentNode.removeChild(el); });
            return clone.innerText;
        """)
        if text and len(text.strip()) > 80:
            return text
    except Exception:
        pass

    # ── 3. Last resort ───────────────────────────────────────────────
    try:
        text = driver.execute_script("return document.body.innerText;")
        if text and len(text.strip()) > 80:
            return text
    except Exception:
        pass

    return None


def handle_sbxh2(driver, novel_url: str, do_translate: bool) -> None:
    """
    Scrape chapters from sbxh2.com (newtokki).

    Key behaviours
    --------------
    * Title    → h1 selector (confirmed working by diagnostics).
    * Chapters → scraped from the novel index page <a> links; episode
                 numbers are mapped to their real (non-sequential) URLs.
    * Content  → innerText of a script/nav-stripped DOM clone, then
                 surgically cleaned with clean_sbxh2_chapter_text().
    * CF check → driver must be launched WITHOUT --headless (handled
                 in main()); 5-second wait added for the JS challenge.
    """
    try:
        parsed   = urlparse(novel_url)
        parts    = parsed.path.strip("/").split("/")
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        if "novel" in parts:
            idx      = parts.index("novel")
            novel_id = parts[idx + 1] if idx + 1 < len(parts) else None
        else:
            novel_id = None

        if not novel_id:
            print(f"{r}[{w}X{r}]{w} Could not parse novel ID from URL.")
            return

        novel_index_url = f"{base_url}/novel/{novel_id}"

        print(f"{T()}[{T2()}!{T()}]{w} Loading novel index page …")
        try:
            driver.get(novel_index_url)
        except TimeoutException:
            driver.execute_script("window.stop();")

        # Block here until Cloudflare clears (up to 2 minutes).
        # The user can solve a CAPTCHA in the browser window if one appears.
        cf_ok = wait_for_cloudflare(driver, timeout=120)
        if not cf_ok:
            print(f"{r}[{w}X{r}]{w} Could not get past Cloudflare. Try again or solve the CAPTCHA manually.")
            return

        # ── grab title AFTER CF cleared ─────────────────────────────
        novel_title = None
        for sel in ["h1", "h2", ".novel-title", ".title", ".book-title"]:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                txt = el.text.strip()
                if txt:
                    novel_title = txt
                    break
            except Exception:
                continue

        if not novel_title:
            # driver.title format: "Novel Name | 뉴토끼"
            raw_title = driver.title or ""
            novel_title = raw_title.split("|")[0].split("–")[0].split("-")[0].strip()
        if not novel_title:
            novel_title = f"Novel_{novel_id}"

        folder_name = re.sub(r'[\\/*?:"<>|]', "-", novel_title).strip()
        folder_path = os.path.join(os.getcwd(), folder_name)
        os.makedirs(folder_path, exist_ok=True)

        print(f"{T()}[{T2()}!{T()}]{w} Novel : {novel_title}")
        print(f"{T()}[{T2()}!{T()}]{w} Folder: {folder_path}")

        # ── Active-settings notification ────────────────────────────
        fmt_disp   = SETTINGS["download_format"].upper()
        tl_disp    = f"{Fore.LIGHTGREEN_EX}ON{Fore.RESET}" if SETTINGS["translate"] else f"{Fore.RED}OFF{Fore.RESET}"
        theme_disp = SETTINGS["theme"]
        print(f"\n{T()}┌─ Active Settings {'─'*31}┐{Fore.RESET}")
        print(f"  {T()}[{T2()}!{T()}]{Fore.WHITE}  Format   : {T()}{fmt_disp}{Fore.RESET}")
        print(f"  {T()}[{T2()}!{T()}]{Fore.WHITE}  Translate: {tl_disp}")
        print(f"  {T()}[{T2()}!{T()}]{Fore.WHITE}  Theme    : {T()}{theme_disp}{Fore.RESET}")
        print(f"  {T()}[{T2()}!{T()}]{Fore.WHITE}  Change settings via option {T()}[3]{Fore.WHITE} from the main menu.{Fore.RESET}")
        print(f"{T()}└{'─'*49}┘{Fore.RESET}\n")

        # Chapter list reads from the CURRENT page (already loaded + CF-cleared)
        chapters = get_chapter_list(driver, novel_index_url)

        if not chapters:
            print(f"{r}[{w}X{r}]{w} No chapters found on index page.")
            return

        first_ep = chapters[0]["ep"]
        last_ep  = chapters[-1]["ep"]
        print(f"{T()}[{T2()}!{T()}]{w} Episodes available: {first_ep} – {last_ep}  ({len(chapters)} total)")

        ep_map = {ch["ep"]: ch for ch in chapters}

        start_raw = input(f"\n{T()}[{T2()}>{T()}]{w} Enter starting episode number (0 to go back): ").strip()
        if start_raw == '0':
            return
        end_raw = input(f"{T()}[{T2()}>{T()}]{w} Enter ending episode number (0 to go back)  : ").strip()
        if end_raw == '0':
            return
        start_ep = int(start_raw)
        end_ep   = int(end_raw)

        download_format = SETTINGS["download_format"]

        selected = [ep_map[ep] for ep in range(start_ep, end_ep + 1) if ep in ep_map]
        missing  = [ep for ep in range(start_ep, end_ep + 1) if ep not in ep_map]
        if missing:
            print(f"{y}[{w}!{y}]{w} Episodes not in chapter list (may be locked/missing): {missing}")

        failed_eps = []

        def try_download(ch: dict) -> bool:
            ep_num   = ch["ep"]
            ep_url   = ch["url"]
            ep_label = ch["title"] or f"Episode {ep_num}"

            print(f"{T()}[{T2()}!{T()}]{w} Episode {ep_num}: {ep_url}")
            try:
                driver.get(ep_url)
            except TimeoutException:
                driver.execute_script("window.stop();")

            # Wait for CF to clear on this chapter page too
            wait_for_cloudflare(driver, timeout=60)

            # Poll until the *cleaned* chapter text is non-empty.
            # Raw body text passes 400 chars even with just nav/headers, so we
            # must clean first and check the result — that way we only proceed
            # once real chapter content is actually on the page.
            raw  = None
            text = None
            for attempt in range(20):
                raw = extract_via_clipboard(driver)
                if raw:
                    text = clean_sbxh2_chapter_text(raw)
                    if text and len(text.strip()) >= 200:
                        break
                    text = None
                    # On 3rd attempt dump diagnostics so we can see what
                    # the page returns vs what survives cleaning
                    if attempt == 2:
                        print(f"{y}[{w}DBG{y}]{w} --- RAW clipboard (first 800 chars) ---")
                        print((raw or "")[:800])
                        print(f"{y}[{w}DBG{y}]{w} --- CLEANED (first 800 chars) ---")
                        print((clean_sbxh2_chapter_text(raw or "") or "<empty after cleaning>")[:800])
                        print(f"{y}[{w}DBG{y}]{w} --- END ---")
                if attempt < 19:
                    print(f"{y}[{w}~{y}]{w} Episode {ep_num}: waiting for content … ({attempt + 1}/20)")
                    time.sleep(1.5)

            if not raw:
                print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} Could not extract text for Episode {ep_num}")
                return False
            if not text:
                print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} Episode {ep_num} was empty after cleaning")
                return False

            if do_translate:
                print(f"{T()}[{T2()}~{T()}]{w} Translating Episode {ep_num} …")
                lines = [l for l in text.split("\n") if l.strip()]
                lines = translate_lines(lines)
                text  = "\n\n".join(lines)

            safe_label = re.sub(r'[\\/*?:"<>|]', '-', ep_label)
            filename = f"Episode {ep_num:04d} - {safe_label}.txt"
            save_to_file(os.path.join(folder_path, filename), text)
            print(f"{gg}[{w}+{gg}]{w} Saved Episode {ep_num}")
            return True

        for ch in selected:
            if not try_download(ch):
                failed_eps.append(ch["ep"])

        while failed_eps:
            print(f"\n{r}[{w}X{r}]{w} Failed episodes: {failed_eps}")
            retry = input(f"{T()}[{T2()}>{T()}]{w} Retry failed episodes? (y/n): ").strip().lower()
            if retry != "y":
                break
            still_failed = []
            for ep_num in failed_eps:
                if ep_num in ep_map:
                    if not try_download(ep_map[ep_num]):
                        still_failed.append(ep_num)
                else:
                    still_failed.append(ep_num)
            failed_eps = still_failed

        if failed_eps:
            print(f"\n{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} Some episodes still failed: {failed_eps}")
        else:
            print(f"\n{gg}[{w}!{gg}]{w} All episodes downloaded successfully.")

        if download_format == "epub":
            save_as_epub(folder_path, novel_title)

        print(f"{T()}[{T2()}!{T()}]{w} Done.")

    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error in sbxh2 handler: {e}")
        import traceback; traceback.print_exc()


# ─────────────────────────────────────────────
#  EXISTING HANDLERS (unchanged)
# ─────────────────────────────────────────────

def lnccreate_novel_folder(driver):
    try:
        current_url = driver.current_url
        parsed = urlparse(current_url)
        parts = parsed.path.strip("/").split("/")

        if "book" in parts:
            book_index = parts.index("book")
            slug = parts[book_index + 1]
        else:
            raise Exception("Could not locate book title in URL")

        novel_title = slug.replace("-", " ").title()
        folder_name = novel_title.replace(":", " -").replace("/", "-")
        folder_path = os.path.join(os.getcwd(), folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{T()}[{T2()}!{T()}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")

        return folder_path

    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error creating novel folder from URL: {e}")
        return None

def lncscrape_chapter(driver, chapter_url, chapter_title, folder_path, max_line_length=80):
    try:
        try:
            driver.get(chapter_url)
        except TimeoutException:
            driver.execute_script("window.stop();")

        time.sleep(1.2)

        container = driver.find_element(By.ID, "chapter-container")

        title_text = ""
        try:
            title_el = driver.find_element(By.CLASS_NAME, "chapter-title")
            title_text = title_el.text.strip()
        except:
            pass

        try:
            content_root = container.find_element(By.CLASS_NAME, "chapter-content")
        except:
            content_root = container

        for ad in content_root.find_elements(By.CSS_SELECTOR, ".nf-ads"):
            driver.execute_script("arguments[0].remove();", ad)

        final_lines = []

        if title_text:
            final_lines.append(title_text)

        paragraphs = content_root.find_elements(By.XPATH, ".//p")

        for p in paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if (
                text.startswith("If you find any errors")
                or text.startswith("Share to your friends")
                or "Tap the middle of the screen" in text
            ):
                break
            if text == title_text:
                continue
            final_lines.append(text)

        if len(final_lines) <= (1 if title_text else 0):
            for line in content_root.text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line == title_text:
                    continue
                if line.startswith("If you find any errors"):
                    break
                final_lines.append(line)

        wrapped = [textwrap.fill(line, width=max_line_length) for line in final_lines]
        final_content = "\n\n".join(wrapped)
        save_to_file(os.path.join(folder_path, f"{chapter_title}.txt"), final_content)
        print(f"{T()}[{T2()}+{T()}]{w} Downloaded {chapter_title}")

    except Exception as e:
        print(f"{r}[{w}x{r}]{w} Error scraping {chapter_title}: {e}")

def lncdownload_chapters(driver, base_url, start_chapter, end_chapter, folder_path):
    for ch_num in range(start_chapter, end_chapter + 1):
        chapter_url = f"{base_url}/chapter-{ch_num}"
        chapter_title = f"Chapter {ch_num}"
        try:
            time.sleep(0.02)
            print(f"{T()}[{T2()}!{T()}] {w}Downloading {chapter_title} from {chapter_url}")
            driver.get(chapter_url)
            lncscrape_chapter(driver, chapter_url, chapter_title, folder_path)
        except Exception as e:
            raise Exception(f"Failed to download chapter {ch_num}: {e}")

def get_chrome_version():
    os_type = platform.system().lower()
    version = None

    try:
        if os_type == "windows":
            output = subprocess.run(
                [r'reg', 'query', r'HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon', '/v', 'version'],
                capture_output=True, text=True
            )
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output.stdout)
            if match:
                version = match.group(1)
        elif os_type == "darwin":
            output = subprocess.run(
                ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"],
                capture_output=True, text=True
            )
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output.stdout)
            if match:
                version = match.group(1)
        elif os_type == "linux":
            for cmd in ["google-chrome", "chrome", "chromium-browser"]:
                try:
                    output = subprocess.run([cmd, "--version"], capture_output=True, text=True)
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output.stdout)
                    if match:
                        version = match.group(1)
                        break
                except FileNotFoundError:
                    continue
    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error detecting Chrome version: {e}")

    if not version:
        raise RuntimeError("Could not detect Chrome version automatically.")
    return version

def download_chromedriver():
    random_loading_small = 0.5
    random_loading_medium = 1
    random_loading_large = 1.5

    os_type = platform.system().lower()
    chrome_driver_path = os.path.join(os.getcwd(), "chromedriver")

    version = get_chrome_version()
    print(f"{T()}[{T2()}!{T()}]{w} Detected Chrome version: {version}")

    if os_type == "windows":
        download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win32/chromedriver-win32.zip"
        driver_file_name = "chromedriver-win32.zip"
    elif os_type == "darwin":
        download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/mac-x64/chromedriver-mac-x64.zip"
        driver_file_name = "chromedriver-mac-x64.zip"
    elif os_type == "linux":
        download_url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/linux64/chromedriver-linux64.zip"
        driver_file_name = "chromedriver-linux64.zip"
    else:
        raise Exception("Unsupported OS")

    zip_file_path = os.path.join(os.getcwd(), driver_file_name)
    time.sleep(random_loading_small)
    print(f"{T()}[{T2()}!{T()}]{w} Downloading ChromeDriver from {download_url}...")
    time.sleep(random_loading_large)

    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(zip_file_path, "wb") as zip_file:
            zip_file.write(response.content)
        time.sleep(random_loading_small)
        print(f"{T()}[{T2()}+{T()}]{w} Downloaded {driver_file_name}. Extracting...")
        time.sleep(random_loading_medium)
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(os.getcwd())
        os.remove(zip_file_path)
        base_folder_name = driver_file_name.replace(".zip", "")
        extracted_folder = os.path.join(os.getcwd(), base_folder_name)

        if os.path.isdir(extracted_folder):
            for item in ["chromedriver.exe", "chromedriver"]:
                item_path = os.path.join(extracted_folder, item)
                if os.path.exists(item_path):
                    new_path = os.path.join(os.getcwd(), os.path.basename(item_path))
                    os.replace(item_path, new_path)
            try:
                os.rmdir(extracted_folder)
            except OSError:
                import shutil
                shutil.rmtree(extracted_folder, ignore_errors=True)
        time.sleep(random_loading_medium)
        print(f"{T()}[{T2()}+{T()}]{w} ChromeDriver extracted and moved successfully.")
        time.sleep(random_loading_large)

        if os_type == "windows":
            chrome_driver_path = os.path.join(os.getcwd(), "chromedriver.exe")

        return chrome_driver_path
    except requests.exceptions.RequestException as e:
        print(f"{Fore.RED}[{Fore.WHITE}x{Fore.RED}]{w} Error downloading ChromeDriver: {e}")
        return None

def check_and_set_driver():
    global chrome_driver_path

    random_loading_small = 0.5
    random_loading_large = 1.5

    if chrome_driver_path == "NONE" or chrome_driver_path == "C:/Program Files":
        driver_exists = input(f"\n{T()}[{T2()}>{T()}]{w} Do you have ChromeDriver? (Y/N): ").strip().lower()

        if driver_exists == "y":
            time.sleep(random_loading_small)
            chrome_driver_path = input(f"{T()}[{T2()}>{T()}]{w} Please input your ChromeDriver path: ").strip()
            print(f"{T()}[{T2()}!{T()}] {w}Driver path set to: {chrome_driver_path}")
        elif driver_exists == "n":
            time.sleep(random_loading_small)
            print(f"{T()}[{T2()}!{T()}]{w} Downloading ChromeDriver for your system...")
            time.sleep(random_loading_large)
            new_driver_path = download_chromedriver()
            if new_driver_path is None:
                time.sleep(random_loading_small)
                print(f"{r}[{w}X{r}]{w}  Failed to download ChromeDriver.")
                time.sleep(4)
                return
            else:
                chrome_driver_path = new_driver_path

        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        config["DRIVERPATH"] = chrome_driver_path

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

        print(f"{T()}[{T2()}!{T()}] {w}Driver path set to: {chrome_driver_path}")

def normalize_novelfire_base_url(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.strip('/').split('/')
    if 'book' in parts:
        book_index = parts.index('book')
        base_path = '/'.join(parts[:book_index + 2])
        return f"{parsed.scheme}://{parsed.netloc}/{base_path}"
    return url.rstrip('/')

def handle_novelfire(driver, novel_url):
    print(f'{T()}[{T2()}+{T()}]{w} NovelFire downloads may be slow.')
    novel_base_url = normalize_novelfire_base_url(novel_url)
    if novel_base_url.endswith('/chapters/'):
        folder_path = os.path.join(os.getcwd(), "Downloaded_Chapters")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        novel_title = "Downloaded_Chapters"
    else:
        driver.get(novel_url)
        folder_path = lnccreate_novel_folder(driver)
        if not folder_path:
            print(f"{T()}[{T2()}!{T()}] {w}Could not create or find folder. Exiting...")
            driver.quit()
            return
        novel_title = os.path.basename(folder_path)

    start_chapter = int(input(f"\n{T()}[{T2()}>{T()}]{w} Enter the starting chapter: "))
    end_chapter = int(input(f"{T()}[{T2()}>{T()}]{w} Enter the ending chapter: "))
    download_format = input(f"{T()}[{T2()}?{T()}]{w} Download format (txt/epub) [default = txt]: ").strip().lower()
    if download_format not in ['txt', 'epub']:
        download_format = 'txt'

    failed_chapters = []

    def try_download(ch_num):
        try:
            lncdownload_chapters(driver, novel_base_url, ch_num, ch_num, folder_path)
            return True
        except Exception as e:
            print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}] {w}Error downloading Chapter {ch_num}: {e}")
            return False

    for ch in range(start_chapter, end_chapter + 1):
        if not try_download(ch):
            failed_chapters.append(ch)

    while failed_chapters:
        print(f"\n{r}[{w}X{r}]{w} The following chapters failed: {failed_chapters}")
        retry = input(f"{T()}[{T2()}>{T()}]{w} Retry these chapters? (y/n): ").strip().lower()
        if retry != "y":
            break
        still_failed = []
        for ch in failed_chapters:
            if not try_download(ch):
                still_failed.append(ch)
        failed_chapters = still_failed

    if failed_chapters:
        print(f"\n{T()}[{T2()}!{T()}] {w}Some chapters still failed: {failed_chapters}")
    else:
        print(f"\n{gg}[{w}!{gg}] {w}All requested chapters downloaded successfully.")
        if download_format == "epub":
            save_as_epub(folder_path, novel_title)

    print(f'{T()}[{T2()}!{T()}] {w}Finished downloading the requested chapters.')

def handle_wetriedtls(driver, novel_url):
    try:
        driver.get(novel_url)
        time.sleep(2)

        novel_title = None
        try:
            title_element = driver.find_element(By.TAG_NAME, "h1")
            novel_title = title_element.text.strip()
        except:
            pass
        if not novel_title:
            try:
                novel_title = driver.title.split("|")[0].strip()
            except:
                novel_title = "Untitled_Novel"

        folder_name = novel_title.replace(':', ' -').replace('/', '-')
        folder_path = os.path.join(os.getcwd(), folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{T()}[{T2()}!{T()}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")

        try:
            chapter_list = driver.find_element(By.CSS_SELECTOR, "ul.grid.grid-cols-1.gap-3")
            chapter_links = chapter_list.find_elements(By.TAG_NAME, "a")
            latest_chap_num = max(int(a.get_attribute("href").split("/")[-1].replace("chapter-", "")) for a in chapter_links)
            print(f"{T()}[{T2()}!{T()}] {w}Latest available chapter: {latest_chap_num}")
        except Exception as e:
            print(f"{y}[{w}!{y}] {w}Could not determine latest chapter: {e}")
            latest_chap_num = None

        while True:
            time.sleep(1)
            start_chapter = int(input(f"\n{T()}[{T2()}>{T()}]{w} Enter the starting chapter: ").strip())
            end_chapter = int(input(f"{T()}[{T2()}>{T()}]{w} Enter the ending chapter: ").strip())
            if latest_chap_num and end_chapter > latest_chap_num:
                print(f"{y}[{w}!{y}] {w}You cannot download beyond chapter {latest_chap_num}.")
            else:
                break

        download_format = input(f"{T()}[{T2()}?{T()}]{w} Download format (txt/epub) [default txt]: ").strip().lower()
        if download_format not in ['txt', 'epub']:
            download_format = 'txt'

        failed_chapters = []

        def try_download(chap_num):
            chapter_url = f"{novel_url.rstrip('/')}/chapter-{chap_num}"
            chapter_title = f"Chapter {chap_num}"
            print(f"{T()}[{T2()}!{T()}] {w}Downloading {chapter_title} from {chapter_url}")
            driver.get(chapter_url)
            try:
                WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "reader-container")))
                container = driver.find_element(By.ID, "reader-container")
                paragraphs = container.find_elements(By.TAG_NAME, "p")
                lines = [p.text.strip() for p in paragraphs if p.text.strip()]
                content = "\n\n".join(lines)
                save_to_file(os.path.join(folder_path, f"{chapter_title}.txt"), content)
                print(f"{T()}[{T2()}+{T()}] {w}Downloaded {chapter_title}")
                return True
            except Exception as e:
                print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}] {w}Error downloading {chapter_title}: {e}")
                return False
            finally:
                time.sleep(random.uniform(0.5, 1.2))

        for chap_num in range(start_chapter, end_chapter + 1):
            if not try_download(chap_num):
                failed_chapters.append(chap_num)

        while failed_chapters:
            print(f"\n{y}[{w}!{y}] {w}The following chapters failed: {failed_chapters}")
            retry = input(f"{T()}[{T2()}?{T()}]{w} Retry these chapters? (y/n): ").strip().lower()
            if retry != "y":
                break
            still_failed = []
            for ch in failed_chapters:
                if not try_download(ch):
                    still_failed.append(ch)
            failed_chapters = still_failed

        if failed_chapters:
            print(f"\n{Fore.RED}[{Fore.WHITE}!{Fore.RED}] {w}Some chapters still failed: {failed_chapters}")
        else:
            print(f"\n{T()}[{T2()}!{T()}] {w}All requested chapters downloaded successfully.")
            if download_format == "epub":
                save_as_epub(folder_path, novel_title)

        print(f"{T()}[{T2()}!{T()}] {w}Finished downloading chapters {start_chapter} to {end_chapter}.")

    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error in WetriedTLS handler: {e}")

def handle_helioscans(driver, novel_url):
    try:
        driver.get(novel_url)
        time.sleep(2)

        novel_title = None
        try:
            title_element = driver.find_element(By.TAG_NAME, "h1")
            novel_title = title_element.text.strip()
        except:
            pass
        if not novel_title:
            try:
                novel_title = driver.title.split("|")[0].strip()
            except:
                novel_title = "Untitled_Novel"
        novel_title = re.sub(r'(\s*[-:]\s*Chapter\s*\d+)$', '', novel_title, flags=re.IGNORECASE)

        folder_name = novel_title.replace(':', ' -').replace('/', '-')
        folder_path = os.path.join(os.getcwd(), folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{T()}[{T2()}+{T()}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}]{w} Folder already exists: {folder_path}")

        WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.ID, "chapters")))
        chapter_elements = driver.find_elements(By.CSS_SELECTOR, "#chapters a.chapter-el")

        chapters = []
        latest_free_chap_num = 0
        for elem in chapter_elements:
            try:
                elem.find_element(By.CSS_SELECTOR, "div.flex.gap-1.justify-center.items-center.w-fit.bg-yellow-200.text-yellow-600")
                is_paid = True
            except:
                is_paid = False

            if not is_paid:
                title = elem.get_attribute("title") or elem.text
                href = elem.get_attribute("href")
                if title and href:
                    chap_num_match = re.search(r'\d+', title)
                    if chap_num_match:
                        chap_num = int(chap_num_match.group())
                        if chap_num > latest_free_chap_num:
                            latest_free_chap_num = chap_num
                        chapters.append((chap_num, title.strip(), href.strip()))

        if not chapters:
            print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} No free chapters found.")
            return

        chapters.sort(key=lambda x: x[0])
        print(f"{T()}[{T2()}!{T()}] {w}Latest free chapter available: {latest_free_chap_num}")

        while True:
            start_chapter = int(input(f"\n{T()}[{T2()}>{T()}]{w} Enter the starting chapter: ").strip())
            end_chapter = int(input(f"{T()}[{T2()}>{T()}]{w} Enter the ending chapter: ").strip())
            if end_chapter > latest_free_chap_num:
                print(f"{y}[{w}!{y}]{w} You cannot download beyond chapter {latest_free_chap_num}.")
            else:
                break

        download_format = input(f"{T()}[{T2()}>{T()}]{w} Download format (txt/epub) [default txt]: ").strip().lower()
        if download_format not in ['txt', 'epub']:
            download_format = 'txt'

        selected = [(num, title, url) for (num, title, url) in chapters if start_chapter <= num <= end_chapter]
        if not selected:
            print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} No chapters in that range.")
            return

        failed_chapters = []

        def try_download(chap_num, chapter_title, chapter_url):
            print(f"{T()}[{T2()}!{T()}] {w}Downloading {chapter_title} from {chapter_url}")
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(chapter_url)
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#pages")))
                pages_container = driver.find_element(By.CSS_SELECTOR, "div#pages")
                reader_container = pages_container.find_element(By.CSS_SELECTOR, "div.novel-reader.default")
                paragraphs = reader_container.find_elements(By.TAG_NAME, "p")
                lines = [p.text.strip() for p in paragraphs if p.text.strip()]
                content = "\n\n".join(lines)
                save_to_file(os.path.join(folder_path, f"Chapter {chap_num}.txt"), content)
                print(f"{T()}[{T2()}+{T()}] {w}Downloaded {chapter_title}")
                return True
            except Exception as e:
                print(f"{r}[{w}X{r}]{w} Error downloading {chapter_title}: {e}")
                return False
            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(random.uniform(0.5, 1.2))

        for chap_num, chapter_title, chapter_url in selected:
            if not try_download(chap_num, chapter_title, chapter_url):
                failed_chapters.append((chap_num, chapter_title, chapter_url))

        while failed_chapters:
            print(f"\n{y}[{w}!{y}]{w} The following chapters failed: {[ch[1] for ch in failed_chapters]}")
            retry = input(f"{T()}[{T2()}?{T()}]{w} Retry these chapters? (y/n): ").strip().lower()
            if retry != "y":
                break
            still_failed = []
            for chap_num, chapter_title, chapter_url in failed_chapters:
                if not try_download(chap_num, chapter_title, chapter_url):
                    still_failed.append((chap_num, chapter_title, chapter_url))
            failed_chapters = still_failed

        if failed_chapters:
            print(f"\n{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} Some chapters still failed: {[ch[1] for ch in failed_chapters]}")
        else:
            print(f"\n{gg}[{w}!{gg}]{w} All requested chapters downloaded successfully.")

        if download_format == "epub":
            save_as_epub(folder_path, novel_title)

        print(f"{T()}[{T2()}!{T()}]{w} Finished downloading chapters {start_chapter} to {end_chapter}.")

    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error in Helioscans handler: {e}")

def handle_webnoveltranslations(driver, novel_url=None):
    try:
        driver.get(novel_url)
        time.sleep(2)
        try:
            title_element = driver.find_element(By.TAG_NAME, "h1")
            novel_title = title_element.text.strip()
        except:
            novel_title = driver.title.split("|")[0].strip()
        novel_title = re.sub(r'(\s*[-:]\s*Chapter\s*\d+)$', '', novel_title, flags=re.IGNORECASE)

        folder_name = novel_title.replace(':', ' -').replace('/', '-')
        folder_path = os.path.join(os.getcwd(), folder_name)
        os.makedirs(folder_path, exist_ok=True)
        start_chapter = int(input(f"\n{T()}[{T2()}>{T()}]{w} Enter the starting chapter: ").strip())
        end_chapter = int(input(f"\n{T()}[{T2()}>{T()}]{w} Enter the ending chapter: ").strip())

        download_format = input(f"\n{T()}[{T2()}>{T()}]{w} Convert to epub or remain txt? (txt/epub): ").strip().lower()
        if download_format not in ['txt', 'epub']:
            download_format = 'txt'

        failed_chapters = []

        def try_download(chap_num):
            if novel_url.endswith("/"):
                chapter_url = f"{novel_url}chapter-{chap_num}/"
            else:
                chapter_url = f"{novel_url}/chapter-{chap_num}/"

            print(f"{T()}[{T2()}!{T()}]{w} Downloading Chapter {chap_num} ({chapter_url})")
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(chapter_url)
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#novel-chapter-container")))
                container = driver.find_element(By.CSS_SELECTOR, "div#novel-chapter-container")
                paragraphs = container.find_elements(By.TAG_NAME, "p")
                lines = [p.text.strip() for p in paragraphs if p.text.strip()]
                if not lines:
                    print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} No text found for Chapter {chap_num}, skipping.")
                    return False
                content = "\n\n".join(lines)
                save_to_file(os.path.join(folder_path, f"Chapter {chap_num}.txt"), content)
                print(f"{T()}[{T2()}!{T()}]{w} Downloaded Chapter {chap_num}")
                return True
            except Exception:
                print(f"Chapter {chap_num} not found or failed to load, skipping.")
                return False
            finally:
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                time.sleep(random.uniform(0.5, 1.2))

        for chap_num in range(start_chapter, end_chapter + 1):
            if not try_download(chap_num):
                failed_chapters.append(chap_num)

        if failed_chapters:
            print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} The following chapters failed or were missing: {failed_chapters}")

        if download_format == "epub":
            save_as_epub(folder_path, novel_title)

        print(f"{T()}[{T2()}!{T()}]{w} Finished downloading chapters {start_chapter} to {end_chapter}.")

    except Exception as e:
        print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}]{w} Error in WebnovelTranslations handler: {e}")


# ─────────────────────────────────────────────
#  SITE HANDLER REGISTRY + DISPATCHER
# ─────────────────────────────────────────────

SITE_HANDLERS = {
    'novelfire': handle_novelfire,
    'wetriedtls': handle_wetriedtls,
    'helioscans': handle_helioscans,
    'webnoveltranslations': handle_webnoveltranslations,
}

def dispatch_handler(driver, novel_url):
    # sbxh uses saved settings — no redundant prompts
    if 'sbxh' in novel_url:
        do_translate = SETTINGS["translate"]
        handle_sbxh2(driver, novel_url, do_translate)
        return

    for site_key, handler_func in SITE_HANDLERS.items():
        if site_key in novel_url:
            handler_func(driver, novel_url)
            return

    print(f"{r}[{w}X{r}]{w} Not a supported site.")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        Spinner()
        check_and_set_driver()
        os.system('cls' if os.name == 'nt' else 'clear')

        titlecard = """
 ▐ ▄        ▌ ▐·▄▄▄ .▄▄▌      .▄▄ ·  ▄▄· ▄▄▄   ▄▄▄·  ▄▄▄·▄▄▄ .▄▄▄  
•█▌▐█▪     ▪█·█▌▀▄.▀·██•      ▐█ ▀. ▐█ ▌▪▀▄ █·▐█ ▀█ ▐█ ▄█▀▄.▀·▀▄ █·
▐█▐▐▌ ▄█▀▄ ▐█▐█•▐▀▀▪▄██▪      ▄▀▀▀█▄██ ▄▄▐▀▀▄ ▄█▀▀█  ██▀·▐▀▀▪▄▐▀▀▄ 
██▐█▌▐█▌.▐▌ ███ ▐█▄▄▌▐█▌▐▌    ▐█▄▪▐█▐███▌▐█•█▌▐█ ▪▐▌▐█▪·•▐█▄▄▌▐█•█▌
▀▀ █▪ ▀█▄▀▪. ▀   ▀▀▀ .▀▀▀      ▀▀▀▀ ·▀▀▀ .▀  ▀ ▀  ▀ .▀    ▀▀▀ .▀  ▀                       
"""
        namecard = """
  ___        _    ___ _    _ _   _         __ _    _    
 | _ )_  _  (_)  / __(_)__| | |_| |_  ___ / _(_)__| |_  
 | _ \ || |  _  | (__| / _` |  _| ' \/ -_)  _| (_-< ' \ 
 |___/\_, | (_)  \___|_\__,_|\__|_||_\___|_| |_/__/_||_|
      |__/                                                                                
"""
        faded_title = _apply_fade(titlecard)
        faded_name  = _apply_fade(namecard)
        print(faded_title)
        time.sleep(.02)
        print(faded_name)
        time.sleep(.02)

        print(f'{T()}[{T2()}!{T()}]{Fore.WHITE} Information: To reset driver path please type "RESET". To Exit type "EXIT"')
        time.sleep(.07)
        print(f'''
{T()}[{T2()}1{T()}]{w} Scrape a novel  {Fore.RESET}|{Fore.RESET}{T()}[{T2()}2{T()}]{w} Convert txt to epub   {Fore.RESET}|{Fore.RESET}{T()}[{T2()}3{T()}]{w} Settings
''')

        choice = input(f'{T()}[{T2()}>{T()}]{w} What would you like to do?: ').strip()

        if choice.lower() == 'exit':
            os.system('cls' if os.name == 'nt' else 'clear')
            Spinner()
            time.sleep(.2)
            sys.exit(0)

        if choice.lower() == 'reset':
            try:
                with open('config.json', 'r') as f: config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                config = {}
            config["DRIVERPATH"] = "NONE"
            with open('config.json', 'w') as f: json.dump(config, f, indent=4)
            print(f"{T()}[{T2()}!{T()}] {w}Driver path has been reset to NONE")
            time.sleep(.67)
            press_any_key()

        if choice == '1':
            os.system('cls' if os.name == 'nt' else 'clear')
            time.sleep(.2)
            Spinner()
            time.sleep(.09)
            os.system('cls' if os.name == 'nt' else 'clear')
            scrapetitle = """
  /$$$$$$                                                  
 /$$__  $$                                                 
| $$  \__/  /$$$$$$$  /$$$$$$  /$$$$$$   /$$$$$$   /$$$$$$ 
|  $$$$$$  /$$_____/ /$$__  $$|____  $$ /$$__  $$ /$$__  $$
 \____  $$| $$      | $$  \__/ /$$$$$$$| $$  \ $$| $$$$$$$$
 /$$  \ $$| $$      | $$      /$$__  $$| $$  | $$| $$_____/
|  $$$$$$/|  $$$$$$$| $$     |  $$$$$$$| $$$$$$$/|  $$$$$$$
 \______/  \_______/|__/      \_______/| $$____/  \_______/
                                       | $$                
                                       | $$                
                                       |__/                
"""
            faded_scrapetitle = _apply_fade(scrapetitle)
            print(faded_scrapetitle)
            novel_url = input(f"{T()}[{T2()}>{T()}]{w} Enter the novel URL (0 to go back, EXIT to exit): ").strip()
            if novel_url == '0' or novel_url.lower() == 'back':
                continue
            if novel_url.lower() == 'exit':
                continue

            # Check supported sites (sbxh included)
            matched = 'sbxh' in novel_url
            if not matched:
                for site_key in SITE_HANDLERS:
                    if site_key in novel_url:
                        matched = True
                        break

            if not matched:
                print(f"{r}[{w}X{r}]{w} Not a supported site. Please enter a valid URL.")
                time.sleep(2)
                continue

            sys.stderr = open(os.devnull, 'w')
            is_sbxh = 'sbxh' in novel_url
            driver = None

            if is_sbxh:
                # ── undetected-chromedriver for Cloudflare sites ──────────
                # IMPORTANT: uc MUST manage its own chromedriver — do NOT pass
                # the path from config here.  uc downloads a patched driver that
                # matches your installed Chrome version and strips all automation
                # flags (navigator.webdriver, missing plugins, chrome.runtime,
                # etc).  Passing a regular chromedriver breaks the patching and
                # causes the infinite CF-challenge loop you saw.
                print(f"{T()}[{T2()}!{T()}]{w} Launching undetected Chrome for Cloudflare bypass …")
                print(f"{T()}[{T2()}!{T()}]{w} uc is managing its own driver — this is intentional.")
                try:
                    uc_options = uc.ChromeOptions()
                    # NOTE: uc.ChromeOptions does NOT support add_experimental_option —
                    # uc patches those flags internally. Adding them here breaks the driver.
                    uc_options.add_argument("--disable-blink-features=AutomationControlled")
                    uc_options.add_argument("--disable-notifications")
                    uc_options.add_argument("--disable-popup-blocking")
                    uc_options.add_argument("--start-maximized")
                    driver = uc.Chrome(
                        options=uc_options,
                        # driver_executable_path intentionally omitted — let uc
                        # auto-download the correct patched driver for your Chrome
                        headless=False,
                        use_subprocess=True,
                        version_main=None,   # auto-detect Chrome version
                    )
                    # Extra JS patch to hide webdriver flag at runtime
                    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                            window.chrome = { runtime: {} };
                        """
                    })
                except Exception as e:
                    print(f"{r}[{w}X{r}]{w} Failed to launch undetected Chrome: {e}")
                    print(f"{y}[{w}!{y}]{w} Run:  pip install undetected-chromedriver --upgrade")
                    time.sleep(3)
                    continue
            else:
                # ── plain selenium for all other sites ────────────────────
                chrome_options = Options()
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--log-level=3")
                chrome_options.add_argument("--disable-logging")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-software-rasterizer")
                chrome_options.add_argument("--disable-images")
                chrome_options.add_argument("--disable-notifications")
                chrome_options.add_argument("--blink-settings=imagesEnabled=false")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
                prefs = {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.fonts": 2,
                    "profile.managed_default_content_settings.media_stream": 2,
                }
                chrome_options.add_experimental_option("prefs", prefs)
                driver_service = Service(executable_path=chrome_driver_path, log_path=os.devnull)
                try:
                    driver = webdriver.Chrome(service=driver_service, options=chrome_options)
                except (ValueError, selenium.common.exceptions.WebDriverException):
                    print(f"{Fore.RED}[{Fore.WHITE}!{Fore.RED}] {w}ChromeDriver not found or invalid.")
                    reset_choice = input(f"{T()}[{T2()}?{T()}]{w} Reset driver path? (y/n): ").strip().lower()
                    if reset_choice == 'y':
                        try:
                            with open('config.json', 'r') as f:
                                config = json.load(f)
                        except (FileNotFoundError, json.JSONDecodeError):
                            config = {}
                        config["DRIVERPATH"] = "NONE"
                        with open('config.json', 'w') as f:
                            json.dump(config, f, indent=4)
                        print(f"{T()}[{T2()}!{T()}] {w}Driver path reset. Please run again.")
                        time.sleep(3)
                        continue
                    else:
                        print(f"{y}[{w}!{y}] {w}Cannot proceed without a valid ChromeDriver.")
                        time.sleep(2)
                        continue

            try:
                dispatch_handler(driver, novel_url)
            finally:
                driver.quit()
                time.sleep(2)
                press_any_key()
                os.system('cls' if os.name == 'nt' else 'clear')

        if choice == '2':
            os.system('cls' if os.name == 'nt' else 'clear')
            time.sleep(0.2)
            Spinner()
            time.sleep(0.09)
            os.system('cls' if os.name == 'nt' else 'clear')
            conversiontitle = """
 $$$$$$\                                                     $$\     
$$  __$$\                                                    $$ |    
$$ /  \__| $$$$$$\  $$$$$$$\ $$\    $$\  $$$$$$\   $$$$$$\ $$$$$$\   
$$ |      $$  __$$\ $$  __$$\\$$\  $$  |$$  __$$\ $$  __$$\\_$$  _|  
$$ |      $$ /  $$ |$$ |  $$ |\$$\$$  / $$$$$$$$ |$$ |  \__| $$ |    
$$ |  $$\ $$ |  $$ |$$ |  $$ | \$$$  /  $$   ____|$$ |       $$ |$$\ 
\$$$$$$  |\$$$$$$  |$$ |  $$ |  \$  /   \$$$$$$$\ $$ |       \$$$$  |
 \______/  \______/ \__|  \__|   \_/     \_______|\__|        \____/
"""
            faded_conversiontitle = _apply_fade(conversiontitle)
            print(faded_conversiontitle)

            folders = [f for f in os.listdir(os.getcwd()) if os.path.isdir(f)]
            if not folders:
                print(f"{r}[{w}X{r}]{w} No folders found in current directory.")
                press_any_key()
                continue

            print(f"{T()}[{T2()}!{T()}]{w} Available folders:")
            for i, folder in enumerate(folders, 1):
                print(f"  {T()}[{T2()}{i}{T()}]{w} {folder}")
            print(f"  {T()}[{T2()}0{T()}]{w} Back to main menu")

            while True:
                folder_choice = input(f"{T()}[{T2()}>{T()}]{w} Select a folder by number (0 to go back): ").strip()
                if folder_choice == '0':
                    break
                if folder_choice.isdigit() and 1 <= int(folder_choice) <= len(folders):
                    folder_path = folders[int(folder_choice) - 1]
                    break
                else:
                    print(f"{Fore.RED}[{Fore.WHITE}X{Fore.RED}]{w} Invalid choice.{Fore.RESET}")
            else:
                press_any_key()
                continue

            if folder_choice == '0':
                continue

            txt_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.txt')]
            # Support both "Chapter N" and "Episode N" filenames
            chapter_nums = {}
            chapter_pattern = re.compile(r'(?:Chapter|Episode)\s*(\d+)', re.IGNORECASE)

            for file in txt_files:
                match = chapter_pattern.search(file)
                if match:
                    chap_num = int(match.group(1))
                    chapter_nums[chap_num] = file

            if not chapter_nums:
                print(f"{r}[{w}X{r}]{w} No chapters found in this folder.")
                press_any_key()
                continue

            sorted_chapters = sorted(chapter_nums.keys())
            ranges = []
            start = sorted_chapters[0]
            prev = start

            for num in sorted_chapters[1:]:
                if num != prev + 1:
                    ranges.append((start, prev))
                    start = num
                prev = num
            ranges.append((start, prev))

            range_strings = [f"{s} - {e}" if s != e else f"{s}" for s, e in ranges]
            print(f"{T()}[{T2()}!{T()}]{w} Chapters {', '.join(range_strings)} are available for conversion.")

            while True:
                conv_choice = input(f"{T()}[{T2()}>{T()}]{w} Convert all chapters or specific range? (ALL / SP / 0 to go back): {Fore.RESET}").strip().upper()
                if conv_choice == '0':
                    break
                if conv_choice in ['ALL', 'SP']:
                    break
                else:
                    print(f"{Fore.RED}[{Fore.WHITE}X{Fore.RED}]{w} Enter ALL, SP, or 0 to go back.{Fore.RESET}")

            if conv_choice == '0':
                continue

            if conv_choice == 'ALL':
                selected_chapters = sorted_chapters
            else:
                while True:
                    try:
                        start_raw = input(f"{T()}[{T2()}>{T()}]{w} Start chapter (0 to go back): {Fore.RESET}").strip()
                        if start_raw == '0':
                            break
                        end_raw = input(f"{T()}[{T2()}>{T()}]{w} End chapter (0 to go back): {Fore.RESET}").strip()
                        if end_raw == '0':
                            break
                        start_chap = int(start_raw)
                        end_chap   = int(end_raw)
                        if start_chap in chapter_nums and end_chap in chapter_nums and start_chap <= end_chap:
                            selected_chapters = [c for c in sorted_chapters if start_chap <= c <= end_chap]
                            break
                        else:
                            print(f"{Fore.RED}[{Fore.WHITE}X{Fore.RED}]{w} Invalid range.{Fore.RESET}")
                    except ValueError:
                        print(f"{Fore.RED}[{Fore.WHITE}X{Fore.RED}]{w} Enter valid numbers.{Fore.RESET}")
                else:
                    continue  # back was chosen inside range picker — skip epub build

            book = epub.EpubBook()
            book.set_identifier(folder_path)
            book.set_title(folder_path)
            book.set_language('en')
            book.add_author("TopStop5's Novelscraper")
            book.add_metadata('DC', 'title', folder_path)
            book.add_metadata('DC', 'creator', 'Novelscraper by TopStop5', {'id': 'creator', 'opf:role': 'aut'})

            for chap_num in selected_chapters:
                file_path = os.path.join(folder_path, chapter_nums[chap_num])
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().replace('\n', '<br/>')
                chapter = epub.EpubHtml(title=f"Chapter {chap_num}", file_name=f"chapter_{chap_num}.xhtml", lang='en')
                chapter.content = f"<h1>Chapter {chap_num}</h1><p>{content}</p>"
                book.add_item(chapter)
                book.spine.append(chapter)
                book.toc.append(epub.Link(f"chapter_{chap_num}.xhtml", f"Chapter {chap_num}", f"chap_{chap_num}"))

            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            epub_name = os.path.join(folder_path, f"{folder_path}.epub")
            epub.write_epub(epub_name, book)
            print(f"EPUB created: {epub_name}")
            press_any_key()

        if choice == '3':
            # ── SETTINGS ──────────────────────────────────────────────────
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                time.sleep(0.1)
                Spinner()
                time.sleep(0.05)
                os.system('cls' if os.name == 'nt' else 'clear')

                settingstitle = """
  $$$$$$\             $$\     $$\     $$\                               
 $$  __$$\            $$ |    $$ |    \__|                              
 $$ /  \__| $$$$$$\ $$$$$$\ $$$$$$\   $$\ $$$$$$$\   $$$$$$\   $$$$$$$\ 
 \$$$$$$\  $$  __$$\\_$$  _|\_$$  _|  $$ |$$  __$$\ $$  __$$\ $$  _____|
  \____$$\ $$$$$$$$ | $$ |    $$ |    $$ |$$ |  $$ |$$ /  $$ |\$$$$$$\  
 $$\   $$ |$$   ____| $$ |$$\ $$ |$$\ $$ |$$ |  $$ |$$ |  $$ | \____$$\ 
 \$$$$$$  |\$$$$$$$\  \$$$$  |\$$$$  |$$ |$$ |  $$ |\$$$$$$$ |$$$$$$$  |
  \______/  \_______|  \____/  \____/ \__|\__|  \__| \____$$ |\_______/ 
                                                     $$\   $$ |          
                                                     \$$$$$$  |          
                                                      \______/           
"""
                print(_apply_fade(settingstitle))

                # Current values
                fmt_val = SETTINGS["download_format"].upper()
                tl_val  = f"{Fore.LIGHTGREEN_EX}ON{Fore.RESET}" if SETTINGS["translate"] else f"{Fore.RED}OFF{Fore.RESET}"
                th_val  = SETTINGS["theme"]

                print(f"{T()}┌─ Current Settings ─────────────────────────────{Fore.RESET}")
                print(f"  {T()}[{T2()}1{T()}]{T2()} Download Format : {T()}{fmt_val}{Fore.RESET}")
                print(f"  {T()}[{T2()}2{T()}]{T2()} Translate KO→EN : {tl_val}")
                print(f"  {T()}[{T2()}3{T()}]{T2()} Theme           : {T()}{th_val}{Fore.RESET}")
                print(f"  {T()}[{T2()}4{T()}]{T2()} Reset all to defaults{Fore.RESET}")
                print(f"  {T()}[{T2()}0{T()}]{T2()} Back to main menu{Fore.RESET}")
                print(f"{T()}└─────────────────────────────────────────────────{Fore.RESET}\n")

                s = input(f"{T()}[{T2()}>{T()}]{T2()} Choose a setting to change: {Fore.RESET}").strip().lower()

                if s == '1':
                    cur = SETTINGS["download_format"]
                    nxt = "epub" if cur == "txt" else "txt"
                    SETTINGS["download_format"] = nxt
                    save_config()
                    print(f"\n{T()}[{T2()}!{T()}]{T2()} Download format set to {T()}{nxt.upper()}{Fore.RESET}")
                    time.sleep(0.8)

                elif s == '2':
                    SETTINGS["translate"] = not SETTINGS["translate"]
                    save_config()
                    state = f"{Fore.LIGHTGREEN_EX}ON{Fore.RESET}" if SETTINGS["translate"] else f"{Fore.RED}OFF{Fore.RESET}"
                    print(f"\n{T()}[{T2()}!{T()}]{T2()} Translation {state}")
                    time.sleep(0.8)

                elif s == '3':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    themepickertitle = """
 $$$$$$$$\ $$\                                                 
 \__$$  __|$$ |                                                
    $$ |   $$$$$$$\   $$$$$$\  $$$$$$\$$$$\   $$$$$$\         
    $$ |   $$  __$$\ $$  __$$\ $$  _$$  _$$\ $$  __$$\        
    $$ |   $$ |  $$ |$$$$$$$$ |$$ / $$ / $$ |$$$$$$$$ |       
    $$ |   $$ |  $$ |$$   ____|$$ | $$ | $$ |$$   ____|       
    $$ |   $$ |  $$ |\$$$$$$$\ $$ | $$ | $$ |\$$$$$$$\        
    \__|   \__|  \__| \_______|\__| \__| \__| \_______|       
"""
                    print(_apply_fade(themepickertitle))
                    print(f"{Fore.WHITE}  Pick a theme:\n")

                    # Build rows of 3, mirroring main menu style:
                    # {c1}[{c2}N{c1}]{c2} name  |  {c1}[{c2}N{c1}]{c2} name  ...
                    rows = []
                    for i, name in enumerate(FADE_THEMES, 1):
                        c1, c2 = _THEME_COLOURS.get(name, (Fore.MAGENTA, Fore.LIGHTMAGENTA_EX))
                        rows.append((c1, c2, i, name))

                    for r in range(0, len(rows), 3):
                        group = rows[r:r+3]
                        parts = []
                        for c1, c2, i, name in group:
                            parts.append(f"{c1}[{c2}{i}{c1}]{c2} {name}")
                        line = f"  {Fore.RESET}|{Fore.RESET}  ".join(parts)
                        print(f"{line}{Fore.RESET}")
                    print()

                    t = input(f"{T()}[{T2()}>{T()}]{T2()} Enter number or name (or 0 to cancel): {Fore.RESET}").strip().lower()
                    if t and t != '0':
                        chosen = None
                        if t.isdigit():
                            idx = int(t) - 1
                            if 0 <= idx < len(FADE_THEMES):
                                chosen = FADE_THEMES[idx]
                        elif t in FADE_THEMES:
                            chosen = t
                        if chosen:
                            SETTINGS["theme"] = chosen
                            save_config()
                            print(_apply_fade(f"\n  Theme set to: {chosen}"))
                            time.sleep(1)
                        else:
                            print(f"{Fore.RED}[{T2()}X{Fore.RED}]{T2()} Unknown theme.{Fore.RESET}")
                            time.sleep(0.8)

                elif s == '4':
                    SETTINGS["download_format"] = "txt"
                    SETTINGS["translate"]        = False
                    SETTINGS["theme"]            = "purplepink"
                    save_config()
                    print(f"\n{T()}[{T2()}!{T()}]{T2()} Settings reset to defaults.{Fore.RESET}")
                    time.sleep(0.9)

                elif s in ('0', 'b', 'back', ''):
                    break

                else:
                    print(f"{Fore.RED}[{T2()}X{Fore.RED}]{T2()} Invalid choice.{Fore.RESET}")
                    time.sleep(0.6)


if __name__ == "__main__":
    main()