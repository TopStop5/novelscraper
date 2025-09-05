import os, time, sys, textwrap, json, requests, random, zipfile, platform, subprocess, re, html, glob
from colorama import Back, Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
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

chrome_browser_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
chrome_driver_path = "NONE"
VERSION = "2.1.1"

if os.path.exists('config.json'):
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            chrome_driver_path = config.get("DRIVERPATH", "NONE")
    except json.JSONDecodeError as e:
        print(f"Error reading config.json: {e}")

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

def dismiss_popup(driver):
    time.sleep(2)
    try:
        agree_button = driver.find_element(By.CSS_SELECTOR, 'button.css-47sehv')
        agree_button.click()
        print(f"{bb}[{w}!{bb}] {w}Skipped popup...")
    except NoSuchElementException as e:
        pass
        print(f"{y}[{w}!{y}] {w}No Pop-up's detected or couldn't click: {e}")

def press_any_key():
    try:
        import msvcrt
        print(f"\n{bb}[{w}#{bb}] {w}Press any key to continue...", end="", flush=True)
        msvcrt.getch()
    except ImportError:
        import sys, tty, termios
        print(f"\n{bb}[{w}#{bb}] {w}Press any key to continue...", end="", flush=True)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def save_as_epub(folder_path, novel_title):
    import os, re, html, glob
    from ebooklib import epub

    def safe_filename(name):
        return re.sub(r'[\\/*?:"<>|]', '-', name).strip()

    def extract_chapter_number(name):
        # Prefer patterns like "chapter 12" or "chapter_12", case-insensitive.
        m = re.search(r'chapter[^0-9]*?(\d+(?:\.\d+)?)', name, flags=re.IGNORECASE)
        if m:
            num = m.group(1)
            try:
                return int(num) if '.' not in num else float(num)
            except:
                return float('inf')
        # fallback: first standalone number
        m2 = re.search(r'(\d+(?:\.\d+)?)', name)
        if m2:
            num = m2.group(1)
            try:
                return int(num) if '.' not in num else float(num)
            except:
                return float('inf')
        return float('inf')

    def natural_key(s):
        # tie-breaker to keep consistent ordering
        parts = re.split(r'(\d+)', s.lower())
        return [int(p) if p.isdigit() else p for p in parts]

    txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
    if not txt_files:
        print(f"{rr}[{w}X{rr}]{w} No .txt files found to convert.")
        return

    # Build a list with extracted numbers, then sort numerically ascending (oldest -> newest).
    files_with_nums = []
    for p in txt_files:
        base = os.path.basename(p)
        num = extract_chapter_number(base)
        files_with_nums.append((num, base, p))

    files_with_nums.sort(key=lambda x: (x[0], natural_key(x[1])))

    sorted_files = [item[2] for item in files_with_nums]

    # Create EPUB
    book = epub.EpubBook()
    book.set_identifier(safe_filename(novel_title.lower()) or "novel")
    book.set_title(novel_title)
    book.set_language("en")
    # Add author metadata properly
    book.add_author("Novelscraper by TopStop5")
    # Also add explicit DC metadata to help some readers (iOS Books)
    try:
        book.add_metadata('DC', 'creator', 'Novelscraper by TopStop5')
        book.add_metadata('DC', 'title', novel_title)
    except Exception:
        # ignore if ebooklib version behaves differently
        pass

    chapters = []
    total_chaps = len(sorted_files)
    zero_pad = len(str(total_chaps))

    for idx, file_path in enumerate(sorted_files, 1):
        fname = os.path.basename(file_path)
        chap_title = os.path.splitext(fname)[0]
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

        # Keep paragraphs split by blank lines
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

def lnccreate_novel_folder(driver):
    try:
        if '/chapters' in driver.current_url:
            print(f"{bb}[{w}!{bb}] {w}Detected chapters list page.")
            title_element = driver.find_element(By.XPATH, "//a[@class='text2row']")
            novel_title = title_element.get_attribute("title").strip()
        else:
            print(f"{bb}[{w}!{bb}] {w}Detected novel home page.")
            title_element = driver.find_element(By.XPATH, "//h1[@itemprop='name' and contains(@class, 'novel-title')]")
            novel_title = title_element.text.strip()
        
        folder_name = novel_title.replace(':', ' -').replace('/', '-')
        folder_path = os.path.join(os.getcwd(), folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{bb}[{w}!{bb}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")
        
        return folder_path
    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error while extracting title or creating folder: {e}")
        return None

def lncscrape_chapter(driver, chapter_url, chapter_title, folder_path, max_line_length=80):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(chapter_url)
    time.sleep(2)
    try:
        chapter_content = driver.find_element(By.ID, "chapter-container").text
        paragraphs = [p.strip() for p in chapter_content.split("\n") if p.strip()]
        wrapped_paragraphs = [textwrap.fill(p, width=max_line_length) for p in paragraphs]
        final_content = "\n\n".join(wrapped_paragraphs)
        save_to_file(os.path.join(folder_path, f"{chapter_title}.txt"), final_content)
        print(f"{bb}[{w}+{bb}] {w}Downloaded {chapter_title}.")
    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error scraping {chapter_title}: {e}")

    driver.close()
    driver.switch_to.window(driver.window_handles[0])

def save_to_file(filename, content):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(content)

def lncdownload_chapters(driver, novel_url, start_chapter, end_chapter, folder_path):
    current_page = 1
    chapters_per_page = 100

    interval_start = start_chapter
    interval_end = min(interval_start + chapters_per_page - 1, end_chapter)

    base_url = novel_url.rstrip('/')
    if '/chapters' not in base_url:
        base_url += '/chapters'

    while interval_start <= end_chapter:
        print(f"{bb}[{w}!{bb}] {w}Processing chapters from {interval_start} to {interval_end}...")

        chapter_downloaded = False

        while interval_start <= interval_end:
            page_url = f"{base_url}?page={current_page}"
            time.sleep(0.02)
            print(f"{bb}[{w}!{bb}] {w}Navigating to {page_url}")
            driver.get(page_url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.XPATH, "//ul[@class='chapter-list']"))
                )
            except Exception as e:
                print(f"{r}[{w}X{r}]{w} Error: Could not load chapters list: {e}")
                return

            chapter_list = driver.find_elements(By.XPATH, "//ul[@class='chapter-list']/li")
            if not chapter_list:
                time.sleep(0.007)
                print(f"{bb}[{w}!{bb}] {w}No chapters found on this page. Moving to the next page.")
                current_page += 1
                continue

            for chapter in chapter_list:
                try:
                    chapter_number_str = chapter.find_element(By.CLASS_NAME, "chapter-no").text.strip()
                    chapter_number = float(chapter_number_str)
                    if chapter_number.is_integer():
                        chapter_number = int(chapter_number)
                    else:
                        continue
                except (ValueError, AttributeError, NoSuchElementException):
                    print(f"{r}[{w}X{r}]{w} Invalid chapter number format. Skipping this entry.")
                    continue

                if interval_start <= chapter_number <= interval_end:
                    chapter_url = chapter.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    chapter_title = f"Chapter {chapter_number}"
                    time.sleep(0.02)
                    print(f"{bb}[{w}!{bb}] {w}Downloading {chapter_title} from {chapter_url}")
                    lncscrape_chapter(driver, chapter_url, chapter_title, folder_path)

                    interval_start = chapter_number + 1
                    chapter_downloaded = True

            if chapter_downloaded:
                current_page += 1
            else:
                print(f"{bb}[{w}!{bb}] {w}No chapters in range found on this page. Moving to the next page.")
                current_page += 1

        interval_start = max(interval_start, interval_end + 1)
        interval_end = min(interval_start + chapters_per_page - 1, end_chapter)
        time.sleep(0.02)
        print(f"{gg}[{w}!{gg}] {w}Finished processing chapters up to {interval_start - 1}. Moving to the next interval.")

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
        raise RuntimeError("Could not detect Chrome version automatically. Please check Chrome installation.")
    return version

def download_chromedriver():
    random_loading_small = 0.5
    random_loading_medium = 1
    random_loading_large = 1.5

    os_type = platform.system().lower()
    chrome_driver_path = os.path.join(os.getcwd(), "chromedriver")

    version = get_chrome_version()
    print(f"{bb}[{w}!{bb}]{w} Detected Chrome version: {version}")

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
    print(f"{bb}[{w}!{bb}]{w} Downloading ChromeDriver from {download_url}...")
    time.sleep(random_loading_large)

    try:
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(zip_file_path, "wb") as zip_file:
            zip_file.write(response.content)
        time.sleep(random_loading_small)
        print(f"{bb}[{w}+{bb}]{w} Downloaded {driver_file_name}. Extracting...")
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
        print(f"{bb}[{w}+{bb}]{w} ChromeDriver extracted and moved successfully.")
        time.sleep(random_loading_large)

        if os_type == "windows":
            chrome_driver_path = os.path.join(os.getcwd(), "chromedriver.exe")

        return chrome_driver_path
    except requests.exceptions.RequestException as e:
        print(f"{rr}[{w}x{rr}]{w} Error downloading ChromeDriver: {e}")
        return None


def check_and_set_driver():
    import json
    import time
    global chrome_driver_path

    random_loading_small = 0.5
    random_loading_large = 1.5

    if chrome_driver_path == "NONE" or chrome_driver_path == "C:/Program Files":
        driver_exists = input(f"\n{bb}[{w}>{bb}]{w} Do you have ChromeDriver? (Y/N): ").strip().lower()

        if driver_exists == "y":
            time.sleep(random_loading_small)
            chrome_driver_path = input(f"{bb}[{w}>{bb}]{w} Please input your ChromeDriver path: ").strip()

        elif driver_exists == "n":
            time.sleep(random_loading_small)
            print(f"{bb}[{w}!{bb}]{w} Downloading ChromeDriver for your system...")
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

        print(f"{bb}[{w}!{bb}] {w}Driver path set to: {chrome_driver_path}")



def handle_novelfire(driver, novel_url):
    print(f'{bb}[{w}+{bb}]{w} NovelFire downloads may be slow, I\'m working to optimize them but in the meantime, try doing it 1 at a time if it takes too long and you get timed out')

    if novel_url.endswith('/chapters/'):
        folder_path = os.path.join(os.getcwd(), "Downloaded_Chapters")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{bb}[{w}+{bb}]{w} Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")
        novel_title = "Downloaded_Chapters"
    else:
        driver.get(novel_url)
        dismiss_popup(driver)
        folder_path = lnccreate_novel_folder(driver)
        if not folder_path:
            print(f"{bb}[{w}!{bb}] {w}Could not create or find folder. Exiting...")
            driver.quit()
            return
        novel_title = os.path.basename(folder_path)

    start_chapter = int(input(f"\n{bb}[{w}>{bb}]{w} Enter the starting chapter: "))
    end_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the ending chapter: "))
    download_format = input(f"{bb}[{w}?{bb}]{w} Download format (txt/epub) [default = txt]: ").strip().lower()
    if download_format not in ['txt', 'epub']:
        download_format = 'txt'

    failed_chapters = []

    def try_download(ch_num):
        try:
            lncdownload_chapters(driver, novel_url, ch_num, ch_num, folder_path)
            return True
        except Exception as e:
            print(f"{rr}[{w}!{rr}] {w}Error downloading Chapter {ch_num}: {e}")
            return False
    for ch in range(start_chapter, end_chapter + 1):
        if not try_download(ch):
            failed_chapters.append(ch)
    while failed_chapters:
        print(f"\n{r}[{w}X{r}]{w} The following chapters failed: {failed_chapters}")
        retry = input(f"{bb}[{w}>{bb}]{w} Retry these chapters? (y/n): ").strip().lower()
        if retry != "y":
            break
        still_failed = []
        for ch in failed_chapters:
            if not try_download(ch):
                still_failed.append(ch)
        failed_chapters = still_failed
    if failed_chapters:
        print(f"\n{bb}[{w}!{bb}] {w}Some chapters still failed after retries: {failed_chapters}")
    else:
        print(f"\n{gg}[{w}!{gg}] {w}All requested chapters downloaded successfully.")
        if download_format == "epub":
            save_as_epub(folder_path, novel_title)

    print(f'{bb}[{w}!{bb}] {w}Finished downloading the requested chapters.')


def handle_wetriedtls(driver, novel_url):
    try:
        driver.get(novel_url)
        time.sleep(2)

        # Get novel title
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

        # Create folder
        folder_name = novel_title.replace(':', ' -').replace('/', '-')
        folder_path = os.path.join(os.getcwd(), folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{bb}[{w}!{bb}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")

        # Find latest chapter available
        try:
            chapter_list = driver.find_element(By.CSS_SELECTOR, "ul.grid.grid-cols-1.gap-3")
            chapter_links = chapter_list.find_elements(By.TAG_NAME, "a")
            latest_chap_num = max(int(a.get_attribute("href").split("/")[-1].replace("chapter-", "")) for a in chapter_links)
            print(f"{bb}[{w}!{bb}] {w}Latest available chapter: {latest_chap_num}")
        except Exception as e:
            print(f"{y}[{w}!{y}] {w}Could not determine latest chapter, proceeding without check: {e}")
            latest_chap_num = None

        # Ask user for chapter range
        while True:
            time.sleep(1)
            start_chapter = int(input(f"\n{bb}[{w}>{bb}]{w} Enter the starting chapter: ").strip())
            end_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the ending chapter: ").strip())
            if latest_chap_num and end_chapter > latest_chap_num:
                print(f"{y}[{w}!{y}] {w}You cannot download beyond chapter {latest_chap_num}. Please try again.")
            else:
                break

        # Ask for download format
        download_format = input(f"{bb}[{w}?{bb}]{w} Download format (txt/epub) [default txt]: ").strip().lower()
        if download_format not in ['txt', 'epub']:
            download_format = 'txt'

        failed_chapters = []

        # Download function
        def try_download(chap_num):
            chapter_url = f"{novel_url.rstrip('/')}/chapter-{chap_num}"
            chapter_title = f"Chapter {chap_num}"
            print(f"{bb}[{w}!{bb}] {w}Downloading {chapter_title} from {chapter_url}")
            driver.get(chapter_url)
            try:
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "reader-container"))
                )
                container = driver.find_element(By.ID, "reader-container")
                paragraphs = container.find_elements(By.TAG_NAME, "p")
                lines = [p.text.strip() for p in paragraphs if p.text.strip()]
                content = "\n\n".join(lines)
                save_to_file(os.path.join(folder_path, f"{chapter_title}.txt"), content)
                print(f"{bb}[{w}+{bb}] {w}Downloaded {chapter_title}")
                return True
            except Exception as e:
                print(f"{rr}[{w}!{rr}] {w}Error downloading {chapter_title}: {e}")
                return False
            finally:
                time.sleep(random.uniform(0.5, 1.2))

        # Download chapters
        for chap_num in range(start_chapter, end_chapter + 1):
            if not try_download(chap_num):
                failed_chapters.append(chap_num)

        # Retry loop for failed chapters
        while failed_chapters:
            print(f"\n{y}[{w}!{y}] {w}The following chapters failed: {failed_chapters}")
            retry = input(f"{bb}[{w}?{bb}]{w} Retry these chapters? (y/n): ").strip().lower()
            if retry != "y":
                break
            still_failed = []
            for ch in failed_chapters:
                if not try_download(ch):
                    still_failed.append(ch)
            failed_chapters = still_failed

        # Show summary and handle EPUB
        if failed_chapters:
            print(f"\n{rr}[{w}!{rr}] {w}Some chapters still failed after retries: {failed_chapters}")
        else:
            print(f"\n{bb}[{w}!{bb}] {w}All requested chapters downloaded successfully.")
            if download_format == "epub":
                save_as_epub(folder_path, novel_title)

        print(f"{bb}[{w}!{bb}] {w}Finished downloading chapters {start_chapter} to {end_chapter}.")

    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error in WetriedTLS handler: {e}")


def handle_helioscans(driver, novel_url):
    import os, re, time, random, html, glob
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from ebooklib import epub

    def save_to_file(path, content):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    def save_as_epub(folder_path, novel_title):
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        if not txt_files:
            print(f"{rr}[{w}X{rr}]{w} No .txt files found to convert.")
            return
        txt_files.sort()  # zero-padded filenames ensure correct order

        book = epub.EpubBook()
        book.set_identifier(novel_title.replace(" ", "_"))
        book.set_title(novel_title)
        book.set_language("en")
        book.add_author("Novelscraper by TopStop5")

        chapters = []
        for idx, file_path in enumerate(txt_files, 1):
            chap_title = os.path.splitext(os.path.basename(file_path))[0]
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            paras = [p.strip() for p in text.split("\n\n") if p.strip()]
            html_content = "".join(f"<p>{html.escape(p)}</p>" for p in paras)

            ch = epub.EpubHtml(title=chap_title, file_name=f"{idx:05d}.xhtml", lang="en")
            ch.content = f"<h1>{chap_title}</h1>{html_content}"
            book.add_item(ch)
            chapters.append(ch)

        book.toc = chapters
        book.spine = ["nav"] + chapters
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        output_path = os.path.join(folder_path, f"{novel_title}.epub")
        epub.write_epub(output_path, book)
        print(f"{bb}[{w}+{bb}] {w}EPUB created: {output_path}")

    try:
        driver.get(novel_url)
        time.sleep(2)

        # Get novel title
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
            print(f"{bb}[{w}+{bb}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}]{w} Folder already exists: {folder_path}")

        # Wait for chapters list
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.ID, "chapters"))
        )
        chapter_elements = driver.find_elements(By.CSS_SELECTOR, "#chapters a.chapter-el")

        chapters = []
        latest_free_chap_num = 0
        for elem in chapter_elements:
            try:
                paid_tag = elem.find_element(
                    By.CSS_SELECTOR,
                    "div.flex.gap-1.justify-center.items-center.w-fit.bg-yellow-200.text-yellow-600"
                )
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
            print(f"{rr}[{w}!{rr}]{w} No free chapters found.")
            return

        chapters.sort(key=lambda x: x[0])
        print(f"{bb}[{w}!{bb}] {w}Latest free chapter available: {latest_free_chap_num}")

        # Ask user for chapter range
        while True:
            start_chapter = int(input(f"\n{bb}[{w}>{bb}]{w} Enter the starting chapter: ").strip())
            end_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the ending chapter: ").strip())
            if end_chapter > latest_free_chap_num:
                print(f"{y}[{w}!{y}]{w} You cannot download beyond chapter {latest_free_chap_num}. Try again.")
            else:
                break

        download_format = input(f"{bb}[{w}>{bb}]{w} Download format (txt/epub) [default txt]: ").strip().lower()
        if download_format not in ['txt', 'epub']:
            download_format = 'txt'

        selected = [(num, title, url) for (num, title, url) in chapters
                    if start_chapter <= num <= end_chapter]
        if not selected:
            print(f"{rr}[{w}!{rr}]{w} No chapters in that range.")
            return

        failed_chapters = []

        def try_download(chap_num, chapter_title, chapter_url):
            print(f"{bb}[{w}!{bb}] {w}Downloading {chapter_title} from {chapter_url}")
            driver.execute_script("window.open('');")
            driver.switch_to.window(driver.window_handles[-1])
            driver.get(chapter_url)
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div#pages"))
                )
                pages_container = driver.find_element(By.CSS_SELECTOR, "div#pages")
                reader_container = pages_container.find_element(
                    By.CSS_SELECTOR, "div.novel-reader.default"
                )
                paragraphs = reader_container.find_elements(By.TAG_NAME, "p")
                lines = [p.text.strip() for p in paragraphs if p.text.strip()]
                content = "\n\n".join(lines)

                # Zero-padded filename
                filename = f"Chapter {chap_num}.txt"
                save_to_file(os.path.join(folder_path, filename), content)
                print(f"{bb}[{w}+{bb}] {w}Downloaded {chapter_title}")
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

        # Retry failed chapters
        while failed_chapters:
            print(f"\n{y}[{w}!{y}]{w} The following chapters failed: {[ch[1] for ch in failed_chapters]}")
            retry = input(f"{bb}[{w}?{bb}]{w} Retry these chapters? (y/n): ").strip().lower()
            if retry != "y":
                break
            still_failed = []
            for chap_num, chapter_title, chapter_url in failed_chapters:
                if not try_download(chap_num, chapter_title, chapter_url):
                    still_failed.append((chap_num, chapter_title, chapter_url))
            failed_chapters = still_failed

        if failed_chapters:
            print(f"\n{rr}[{w}!{rr}]{w} Some chapters still failed: {[ch[1] for ch in failed_chapters]}")
        else:
            print(f"\n{gg}[{w}!{gg}]{w} All requested chapters downloaded successfully.")

        if download_format == "epub":
            save_as_epub(folder_path, novel_title)

        print(f"{gg}[{w}!{gg}]{w} Finished downloading chapters {start_chapter} to {end_chapter}.")

    except Exception as e:
        print(f"{r}[{w}X{r}]{w} Error in Helioscans handler: {e}")


SITE_HANDLERS = {
    'novelfire': handle_novelfire,
    'wetriedtls': handle_wetriedtls,
    'helioscans': handle_helioscans
}



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
        faded_title = fade.purplepink(titlecard)
        faded_name = fade.pinkred(namecard)
        print(faded_title)
        time.sleep(.02)
        print(faded_name)
        time.sleep(.02)

        print(f'{y}[{w}!{y}] Information: To reset driver path please type "RESET". To Exit type "EXIT"')
        time.sleep(.07)
        print(f'''
{lr}[{w}1{lr}]{w} Scrape a novel  {b}|{Fore.RESET}{lr}[{w}2{lr}]{w} Convert txt to epub   {b}|{Fore.RESET}{lr}[{w}3{lr}]{w} [BLANK]
''')

        choice = input(f'{bb}[{w}>{bb}]{w} What would you like to do?: ').strip()

        if choice.lower() == 'exit':
            os.system('cls' if os.name == 'nt' else 'clear')
            Spinner()
            time.sleep(.2)
            sys.exit(0)

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
            faded_scrapetitle =  fade.purplepink(scrapetitle)
            print(faded_scrapetitle)
            novel_url = input(f"{bb}[{w}>{bb}]{w} Enter the novel URL (type EXIT to exit): ").strip()
            if novel_url.lower() == 'exit':
                continue

            matched_handler = None
            for site_key, handler_func in SITE_HANDLERS.items():
                if site_key in novel_url:
                    matched_handler = handler_func
                    break

            if not matched_handler:
                print("Not a supported site. Please enter a valid URL.")
                time.sleep(2)
                continue

            sys.stderr = open(os.devnull, 'w')
            chrome_options = Options()
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--log-level=3")            
            chrome_options.add_argument("--disable-logging")          
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-software-rasterizer")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
            driver_service = Service(executable_path=chrome_driver_path, log_path=os.devnull)
            try:
                driver = webdriver.Chrome(service=driver_service, options=chrome_options)
            except (ValueError, selenium.common.exceptions.WebDriverException):
                print(f"{rr}[{w}!{rr}] {w}ChromeDriver not found or invalid.")
                reset_choice = input(f"{bb}[{w}?{bb}]{w} Would you like to reset the driver path to reinstall ChromeDriver? (y/n): ").strip().lower()
                if reset_choice == 'y':
                    try:
                        with open('config.json', 'r') as f:
                            config = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        config = {}

                    config["DRIVERPATH"] = "NONE"

                    with open('config.json', 'w') as f:
                        json.dump(config, f, indent=4)

                    print(f"{bb}[{w}!{bb}] {w}Driver path has been reset to NONE. Please run the program again to set a new path.")
                    time.sleep(3)
                    continue
                else:
                    print(f"{y}[{w}!{y}] {w}Cannot proceed without a valid ChromeDriver.")
                    time.sleep(2)
                    continue
            try:
                matched_handler(driver, novel_url)
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
            faded_conversiontitle =  fade.purplepink(conversiontitle)
            print(faded_conversiontitle)
            # List folders in current directory
            folders = [f for f in os.listdir(os.getcwd()) if os.path.isdir(f)]
            if not folders:
                print(f"{r}[{w}X{r}]{w} No folders found in current directory.")
                press_any_key()
                return

            print(f"{bb}[{w}!{bb}]{w} Available folders:")
            for i, folder in enumerate(folders, 1):
                print(f"{m}[{w}{i}{m}]{w} {folder}")

            while True:
                folder_choice = input(f"{bb}[{w}>{bb}]{w} Select a folder by number: ").strip()
                if folder_choice.isdigit() and 1 <= int(folder_choice) <= len(folders):
                    folder_path = folders[int(folder_choice) - 1]
                    break
                else:
                    print(f"{r}[{w}X{r}]{w}  Invalid choice. Enter a number corresponding to a folder.")

            # Collect txt files and chapter numbers
            txt_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.txt')]
            chapter_nums = {}
            chapter_pattern = re.compile(r'Chapter\s*(\d+)', re.IGNORECASE)

            for file in txt_files:
                match = chapter_pattern.search(file)
                if match:
                    chap_num = int(match.group(1))
                    chapter_nums[chap_num] = file

            if not chapter_nums:
                print(f"{r}[{w}X{r}]{w}  No chapters found in this folder.")
                press_any_key()
                return

            # Find consecutive chapter ranges
            sorted_chapters = sorted(chapter_nums.keys())
            ranges = []
            start = sorted_chapters[0]
            prev = start

            for num in sorted_chapters[1:]:
                if num != prev + 1:
                    ranges.append((start, prev))
                    start = num
                prev = num
            ranges.append((start, prev))  # add last range

            # Print available ranges
            range_strings = [f"{s} - {e}" if s != e else f"{s}" for s, e in ranges]
            print(f"{bb}[{w}!{bb}]{w} Chapters {', '.join(range_strings)} are available for conversion.")

            # Ask whether to convert all or specific
            while True:
                conv_choice = input("Convert all chapters or specific range? (ALL/SP): ").strip().upper()
                if conv_choice in ['ALL', 'SP']:
                    break
                else:
                    print("Enter ALL for all chapters, or SP for a specific range.")

            if conv_choice == 'ALL':
                selected_chapters = sorted_chapters
            else:
                while True:
                    try:
                        start_chap = int(input("Start chapter: ").strip())
                        end_chap = int(input("End chapter: ").strip())
                        if start_chap in chapter_nums and end_chap in chapter_nums and start_chap <= end_chap:
                            selected_chapters = [c for c in sorted_chapters if start_chap <= c <= end_chap]
                            break
                        else:
                            print("Invalid range. Chapters must exist and start <= end.")
                    except ValueError:
                        print("Enter valid numbers.")

            # Create EPUB
            book = epub.EpubBook()
            book.set_identifier(folder_path)
            book.set_title(folder_path)
            book.set_language('en')
            book.add_author('Novelscraper by TopStop5')
            book.add_metadata('DC', 'title', folder_path)
            book.add_metadata('DC', 'creator', 'Novelscraper by TopStop5', {'id': 'creator', 'opf:role': 'aut'})

            for chap_num in selected_chapters:
                file_path = os.path.join(folder_path, chapter_nums[chap_num])
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().replace('\n', '<br/>')  # convert paragraphs to <br/>
                chapter = epub.EpubHtml(title=f"Chapter {chap_num}", file_name=f"chapter_{chap_num}.xhtml", lang='en')
                chapter.content = f"<h1>Chapter {chap_num}</h1><p>{content}</p>"
                book.add_item(chapter)
                book.spine.append(chapter)
                book.toc.append(epub.Link(f"chapter_{chap_num}.xhtml", f"Chapter {chap_num}", f"chap_{chap_num}"))

            # Add default NCX and Nav files
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # Write EPUB
            epub_name = os.path.join(folder_path, f"{folder_path}.epub")
            epub.write_epub(epub_name, book)
            print(f"EPUB created: {epub_name}")
            press_any_key()


if __name__ == "__main__":
    main()