import os, time, sys, textwrap, json
from colorama import Back, Fore, Style
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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
    os.system("pip install selenium==4.26.1")
    import selenium

chrome_browser_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"  # Path to your Chrome browser
chrome_driver_path = "NONE"
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

def Spinner():
	l = ['|', '/', '-', '\\', ' ']
	for i in l+l+l:
		sys.stdout.write(f"""\r {i}""")
		sys.stdout.flush()
		time.sleep(0.1)

def dismiss_popup(driver):
    time.sleep(2)
    try:
        agree_button = driver.find_element(By.CSS_SELECTOR, 'button.css-47sehv')  # CSS selector for the AGREE button
        agree_button.click()
        print(f"{g}[{w}!{g}] {w}Skipped popup...")
    except Exception as e:
        pass
        print(f"{y}[{w}!{y}] {w}No Pop-up\'s detected or couldn't click: {e}")

def create_novel_folder(driver):
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

def scrape_chapter(driver, chapter_url, chapter_title, folder_path, max_line_length=80):
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

def download_chapters(driver, novel_url, start_chapter, end_chapter, folder_path):
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
                print(f"{g}[{w}!{g}] {w}No chapters found on this page. Moving to the next page.")
                current_page += 1
                continue

            for chapter in chapter_list:
                try:
                    chapter_number = float(chapter.get_attribute("data-chapterno"))
                    if chapter_number.is_integer():
                        chapter_number = int(chapter_number)
                    else:
                        continue
                except (ValueError, AttributeError):
                    print(f"{rr}[{w}!{rr}] {w}Invalid chapter number format. Skipping this entry.")
                    continue

                if interval_start <= chapter_number <= interval_end:
                    chapter_url = chapter.find_element(By.TAG_NAME, 'a').get_attribute('href')
                    chapter_title = f"Chapter {chapter_number}"
                    print(f"{g}[{w}!{g}] {w}Downloading {chapter_title} from {chapter_url}")
                    scrape_chapter(driver, chapter_url, chapter_title, folder_path)

                    interval_start = chapter_number + 1
                    chapter_downloaded = True

            if chapter_downloaded:
                current_page += 1
            else:
                print(f"{g}[{w}!{g}] {w}No chapters in range found on this page. Moving to the next page.")
                current_page += 1

        interval_start = max(interval_start, interval_end + 1)
        interval_end = min(interval_start + chapters_per_page - 1, end_chapter)
        print(f"{gg}[{w}!{gg}] {w}Finished processing chapters up to {interval_start - 1}. Moving to the next interval.")


def main():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        Spinner()
        global chrome_driver_path

        if chrome_driver_path == "NONE" or chrome_driver_path == "C:/Program Files":
            # If the path is "NONE" or the default, prompt for input
            chrome_driver_path = input(f'{bb}[{w}>{bb}]{w} Please input your chrome driver path: ')

            # Update the config file with the new chrome driver path
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                config = {}

            config["DRIVERPATH"] = chrome_driver_path

            # Write the updated configuration to the JSON file
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)

        else:
            pass
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
        print(faded_name)
        print('To reset driver path please type RESET')
        
        novel_url = input(f"{bb}[{w}>{bb}]{w} Enter the novel URL (type EXIT to exit): ").strip().lower()
        supported_sites = ('lightnovelcave', 'exit', 'reset')
        
        if not any(site in novel_url for site in supported_sites):
            print("Not a supported site. Please enter a valid URL.")
            time.sleep(2)
            continue

        if novel_url == 'reset':
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                config = {}

            config["DRIVERPATH"] = "C:/Program Files"

            # Write the updated configuration to the JSON file
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)

            print(f"{g}[{w}!{g}] {w}Driver path has been reset to C:/Program Files.")
            time.sleep(2)
            os.system('cls' if os.name == 'nt' else 'clear')
            sys.exit(0)
        
        if novel_url == 'exit':
            os.system('cls' if os.name == 'nt' else 'clear')
            Spinner()
            time.sleep(.2)
            sys.exit(0)
        
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--log-level=3")

        driver_service = Service(executable_path=chrome_driver_path)
        driver = webdriver.Chrome(service=driver_service, options=chrome_options)

        if novel_url.endswith('/chapters/'):
            folder_path = os.path.join(os.getcwd(), "Downloaded_Chapters")
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                print(f"Created folder: {folder_path}")
            else:
                print(f"{y}[{w}!{y}] {w}Folder already exists: {folder_path}")
        else:
            driver.get(novel_url)
            dismiss_popup(driver)
            folder_path = create_novel_folder(driver)
            if not folder_path:
                print(f"{g}[{w}!{g}] {w}Could not create or find folder. Exiting...")
                driver.quit()
                return

        start_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the starting chapter: "))
        end_chapter = int(input(f"{bb}[{w}>{bb}]{w} Enter the ending chapter: "))

        download_chapters(driver, novel_url, start_chapter, end_chapter, folder_path)

        print(f'{g}[{w}!{g}] {w}Finished downloading the requested chapters. Exiting...')    

        driver.quit()
        time.sleep(2)
        os.system('cls' if os.name == 'nt' else 'clear')    
        break
if __name__ == "__main__":
    main()