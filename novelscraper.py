import os, time, sys, textwrap, json, requests, random, zipfile, platform, subprocess, re
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
VERSION = "2.0"

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
        print(f"{g}[{w}!{g}] {w}Skipped popup...")
    except NoSuchElementException as e:
        pass
        print(f"{y}[{w}!{y}] {w}No Pop-up's detected or couldn't click: {e}")

def press_any_key():
    """Wait for user to press any key (cross-platform)."""
    try:
        import msvcrt
        print("\nPress any key to continue...", end="", flush=True)
        msvcrt.getch()
    except ImportError:
        import sys, tty, termios
        print("\nPress any key to continue...", end="", flush=True)
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def lnccreate_novel_folder(driver):
    try:
        if '/chapters' in driver.current_url:
            print(f"{g}[{w}!{g}] {w}Detected chapters list page.")
            title_element = driver.find_element(By.XPATH, "//a[@class='text2row']")
            novel_title = title_element.get_attribute("title").strip()
        else:
            print(f"{g}[{w}!{g}] {w}Detected novel home page.")
            title_element = driver.find_element(By.XPATH, "//h1[@itemprop='name' and contains(@class, 'novel-title')]")
            novel_title = title_element.text.strip()
        
        folder_name = novel_title.replace(':', ' -').replace('/', '-')
        folder_path = os.path.join(os.getcwd(), folder_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{g}[{w}!{g}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")
        
        return folder_path
    except Exception as e:
        print(f"{rr}[{w}!{rr}] {w}Error while extracting title or creating folder: {e}")
        return None

def lncscrape_chapter(driver, chapter_url, chapter_title, folder_path, max_line_length=80):
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(chapter_url)
    time.sleep(2)
    try:
        chapter_content = driver.find_element(By.ID, "chapter-container").text
        wrapped_content = textwrap.fill(chapter_content, width=max_line_length)
        save_to_file(os.path.join(folder_path, f"{chapter_title}.txt"), wrapped_content)
        print(f"{g}[{w}!{g}] {w}Downloaded {chapter_title}.")
    except Exception as e:
        print(f"{rr}[{w}!{rr}] {w}Error scraping {chapter_title}: {e}")

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
        print(f"{g}[{w}!{g}] {w}Processing chapters from {interval_start} to {interval_end}...")

        chapter_downloaded = False

        while interval_start <= interval_end:
            page_url = f"{base_url}?page={current_page}"
            time.sleep(0.02)
            print(f"{g}[{w}!{g}] {w}Navigating to {page_url}")
            driver.get(page_url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.XPATH, "//ul[@class='chapter-list']"))
                )
            except Exception as e:
                print(f"{rr}[{w}!{rr}] {w}Error: Could not load chapters list: {e}")
                return

            chapter_list = driver.find_elements(By.XPATH, "//ul[@class='chapter-list']/li")
            if not chapter_list:
                time.sleep(0.007)
                print(f"{g}[{w}!{g}] {w}No chapters found on this page. Moving to the next page.")
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
                    print(f"{rr}[{w}!{rr}] {w}Invalid chapter number format. Skipping this entry.")
                    continue

                if interval_start <= chapter_number <= interval_end:
                    chapter_url = chapter.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    chapter_title = f"Chapter {chapter_number}"
                    time.sleep(0.02)
                    print(f"{g}[{w}!{g}] {w}Downloading {chapter_title} from {chapter_url}")
                    lncscrape_chapter(driver, chapter_url, chapter_title, folder_path)

                    interval_start = chapter_number + 1
                    chapter_downloaded = True

            if chapter_downloaded:
                current_page += 1
            else:
                print(f"{g}[{w}!{g}] {w}No chapters in range found on this page. Moving to the next page.")
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
        print(f"[x] Error detecting Chrome version: {e}")

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
        print(f"{bb}[{w}!{bb}]{w} Downloaded {driver_file_name}. Extracting...")
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
        print(f"{bb}[{g}+{bb}]{w} ChromeDriver extracted and moved successfully.")
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
                print(f"{lr}[{w}!{lr}]{w} Failed to download ChromeDriver.")
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

        print(f"{g}[{w}!{g}]{w} Driver path set to: {chrome_driver_path}")

def handle_novelfire(driver, novel_url):
    print(f'{bb}[{w}+{bb}]{w} NovelFire downloads may be slow, I\'m working to optimize them but in the meantime, try doing it 1 at a time if it takes too long and you get timed out')
    if novel_url.endswith('/chapters/'):
        folder_path = os.path.join(os.getcwd(), "Downloaded_Chapters")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"{bb}[{g}+{bb}]{w} Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")
    else:
        driver.get(novel_url)
        dismiss_popup(driver)
        folder_path = lnccreate_novel_folder(driver)
        if not folder_path:
            print(f"{g}[{w}!{g}] {w}Could not create or find folder. Exiting...")
            driver.quit()
            return

    start_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the starting chapter: "))
    end_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the ending chapter: "))

    lncdownload_chapters(driver, novel_url, start_chapter, end_chapter, folder_path)

    print(f'{g}[{w}!{g}] {w}Finished downloading the requested chapters.')

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
            print(f"{g}[{w}!{g}] {w}Created folder: {folder_path}")
        else:
            print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")

        start_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the starting chapter: "))
        end_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the ending chapter: "))

        for chap_num in range(start_chapter, end_chapter + 1):
            chapter_url = f"{novel_url.rstrip('/')}/chapter-{chap_num}"
            chapter_title = f"Chapter {chap_num}"
            print(f"{g}[{w}!{g}] {w}Downloading {chapter_title} from {chapter_url}")

            driver.get(chapter_url)
            try:
                WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.ID, "reader-container"))
                )
                container = driver.find_element(By.ID, "reader-container")
                paragraphs = container.find_elements(By.TAG_NAME, "p")
                lines = [p.text.strip() for p in paragraphs if p.text.strip()]
                content = "\n".join(lines)
                save_to_file(os.path.join(folder_path, f"{chapter_title}.txt"), content)
                print(f"{g}[{w}!{g}] {w}Downloaded {chapter_title}")
            except Exception as e:
                print(f"{rr}[{w}!{rr}] {w}Error downloading {chapter_title}: {e}")

            time.sleep(random.uniform(0.5, 1.2))

        print(f"{gg}[{w}!{gg}] {w}Finished downloading chapters {start_chapter} to {end_chapter}.")

    except Exception as e:
        print(f"{rr}[{w}!{rr}] {w}Error in WetriedTLS handler: {e}")

SITE_HANDLERS = {
    'novelfire': handle_novelfire,
    'wetriedtls': handle_wetriedtls
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
        print(f'Loading {bb}[{w}VERSION{bb}] {lm}{VERSION}')
        time.sleep(random_loading_medium)
        print(f'{bb}[{w}!{bb}]{w} Version: {lm}{VERSION} {w}Loaded!')
        time.sleep(random_loading_small)
        os.system('cls' if os.name == 'nt' else 'clear')
        faded_title = fade.purplepink(titlecard)
        faded_name = fade.pinkred(namecard)
        print(faded_title)
        time.sleep(.02)
        print(faded_name)
        time.sleep(.02)
        print(f'{y}[{w}!{y}] Information: To reset driver path please type "RESET". To Exit type "EXIT"')
        time.sleep(.07)
        novel_url = input(f"{bb}[{w}>{bb}]{w} Enter the novel URL (type EXIT to exit): ").strip().lower()
        supported_sites = ('wetriedtls', 'novelfire', 'exit', 'reset', 'path')
        
        if not any(site in novel_url for site in supported_sites):
            print("Not a supported site. Please enter a valid URL.")
            time.sleep(2)
            continue

        if novel_url == 'path':
            Spinner()
            print(f"{g}[{w}!{g}] {w}{chrome_driver_path}")
            time.sleep(5)

            continue

        if novel_url == 'reset':
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                config = {}

            config["DRIVERPATH"] = "NONE"

            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)

            print(f"{g}[{w}!{g}] {w}Driver path has been reset to NONE")
            time.sleep(2)
            os.system('cls' if os.name == 'nt' else 'clear')
            sys.exit(0)
        
        if novel_url == 'exit':
            os.system('cls' if os.name == 'nt' else 'clear')
            Spinner()
            time.sleep(.2)
            sys.exit(0)
        
        matched_handler = None
        for site_key, handler_func in SITE_HANDLERS.items():
            if site_key in novel_url:
                matched_handler = handler_func
                break

        if not matched_handler:
            print("Not a supported site. Please enter a valid URL.")
            time.sleep(2)
            continue

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
        driver = webdriver.Chrome(service=driver_service, options=chrome_options)
        matched_handler(driver, novel_url)

        driver.quit()
        time.sleep(2)
        os.system('cls' if os.name == 'nt' else 'clear')

        press_any_key()
if __name__ == "__main__":
    main()