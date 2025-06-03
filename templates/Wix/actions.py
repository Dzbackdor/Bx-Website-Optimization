import time
import random
import os
import sys
import importlib.util
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# Tambahkan import untuk BeautifulSoup
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("⚠️ BeautifulSoup4 tidak terinstall. Install dengan: pip install beautifulsoup4")
    BeautifulSoup = None

# Import colors dari main.py jika tersedia
try:
    from colorama import Fore
    R = Fore.RED
    G = Fore.GREEN
    W = Fore.WHITE
    Y = Fore.YELLOW
except ImportError:
    R = G = W = Y = ""

def pindahkan_akun_ke_limit(email, password):
    """
    Memindahkan akun yang terkena limit ke file akunlimit.txt dan menghapus dari akun.txt
    """
    try:
        # Simpan ke akunlimit.txt
        with open('akunlimit.txt', 'a', encoding='utf-8') as file:
            file.write(f"{email}\n{password}\n")
        print(f"{Y}Akun {email} dipindahkan ke akunlimit.txt{W}")
        
        # Baca semua akun dari akun.txt
        if os.path.exists('akun.txt'):
            with open('akun.txt', 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file if line.strip()]
            
            # Hapus akun yang terkena limit (2 baris pertama)
            if len(lines) >= 2:
                lines_baru = lines[2:]  # Ambil dari baris ke-3 dst
                
                # Tulis ulang file akun.txt tanpa akun yang terkena limit
                with open('akun.txt', 'w', encoding='utf-8') as file:
                    for line in lines_baru:
                        file.write(line + '\n')
                
                print(f"{G}Akun {email} berhasil dihapus dari akun.txt")
                return True
            else:
                print(f"{Y}Tidak ada akun lain di akun.txt")
                return False
        
        return False
        
    except Exception as e:
        print(f"{R}Error saat memindahkan akun ke limit: {W}{e}")
        return False

def cek_akun_terkena_limit(driver, logger=None):
    """
    Mengecek apakah ada class="gPpQmL" yang menandakan akun terkena limit
    """
    try:
        if logger:
            logger.info("🔍 [Wix] Mengecek status akun...")
        
        if not BeautifulSoup:
            if logger:
                logger.warning("⚠️ [Wix] BeautifulSoup tidak tersedia, skip pengecekan limit")
            return False
        
        # Ambil HTML halaman
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Cari elemen dengan class="gPpQmL"
        elemen_limit = soup.find(class_="gPpQmL")
        
        if elemen_limit:
            if logger:
                logger.error(f"❌ [Wix] Terdeteksi class='gPpQmL' - Akun terkena limit!")
                logger.error(f"🚫 [Wix] Element limit: {elemen_limit}")
            else:
                print(f"{R}Terdeteksi class='gPpQmL' - Akun terkena limit!")
            return True
        else:
            if logger:
                logger.info(f"✅ [Wix] [info] Tidak ada class='gPpQmL' - Akun normal")
            else:
                print(f"{G}Tidak ada class='gPpQmL' - Akun normal")
            return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ [Wix] Error saat mengecek limit akun: {e}")
        else:
            print(f"{R}Error saat mengecek limit akun: {W}{e}")
        return False

def load_module_from_path(module_name, file_path):
    """
    Load module dari path secara dinamis
    """
    try:
        if os.path.exists(file_path):
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        else:
            print(f"❌ File tidak ditemukan: {file_path}")
            return None
    except Exception as e:
        print(f"❌ Error loading module {module_name}: {e}")
        return None


def post_comment_with_retry_limit(driver, comment_data, comment_template, signature_data, bot_instance=None, max_retries=3):
    """
    Post comment dengan batas maksimal retry untuk mencegah infinite loop
    """
    logger = bot_instance.logger if bot_instance else None
    
    for attempt in range(max_retries):
        if logger:
            logger.info(f"🔄 [Wix] Attempt {attempt + 1}/{max_retries}")
        
        # Cek apakah masih ada akun tersedia
        if not os.path.exists('akun.txt'):
            if logger:
                logger.error("❌ [Wix] File akun.txt tidak ditemukan")
            return False, driver.current_url
        
        with open('akun.txt', 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
        
        if len(lines) < 2:
            if logger:
                logger.error("❌ [Wix] Tidak ada akun tersisa")
            return False, driver.current_url
        
        # Coba post comment
        success, final_url = post_comment(driver, comment_data, comment_template, signature_data, bot_instance)
        
        if success:
            return True, final_url
        
        if logger:
            logger.warning(f"⚠️ [Wix] Attempt {attempt + 1} gagal, mencoba lagi...")
    
    if logger:
        logger.error(f"❌ [Wix] Semua {max_retries} attempts gagal")
    return False, driver.current_url


def cek_akun_tersedia():
    """
    Cek apakah masih ada akun tersedia di akun.txt
    """
    try:
        if not os.path.exists('akun.txt'):
            return False, 0
        
        with open('akun.txt', 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
        
        jumlah_akun = len(lines) // 2
        return jumlah_akun > 0, jumlah_akun
        
    except Exception as e:
        print(f"{R}Error cek akun tersedia: {W}{e}")
        return False, 0

def get_current_account_info():
    """
    Ambil info akun yang sedang digunakan (2 baris pertama)
    """
    try:
        if not os.path.exists('akun.txt'):
            return None, None
        
        with open('akun.txt', 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
        
        if len(lines) >= 2:
            return lines[0], lines[1]  # email, password
        
        return None, None
        
    except Exception as e:
        print(f"{R}Error get current account: {W}{e}")
        return None, None



def cleanup_popups_once(driver, logger=None):
    """
    Membersihkan popup hanya 1 kali - DIPERBAIKI MENGGUNAKAN TEKNIK YANG SAMA
    """
    try:
        if logger:
            logger.info("🔍 Mencari popup yang perlu dibersihkan...")
        
        # ✅ GUNAKAN SELECTOR YANG SAMA DENGAN cleanup_popups()
        popup_selectors = [
            'button#close.ng-scope',
            'button[id="close"][class="ng-scope"]',
            'button#close[aria-label="Close"]',
            '#close.ng-scope',
            # ✅ TAMBAHAN SELECTOR UMUM
            "[aria-label='Close']",
            "[aria-label='close']",
            ".close-button",
            ".close",
            "[data-hook='close-button']",
            "[data-testid='close-button']",
            ".modal-close",
            "[data-dismiss='modal']"
        ]
        
        popup_ditutup = False
        
        # ✅ GUNAKAN TEKNIK YANG SAMA PERSIS
        for selector in popup_selectors:
            try:
                popup_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for popup in popup_elements:
                    if popup.is_displayed():
                        if logger:
                            logger.info(f"🚨 Popup ditemukan: {selector}")
                        
                        # ✅ METHOD 1: KLIK LANGSUNG
                        try:
                            popup.click()
                            if logger:
                                logger.info("✓ Popup ditutup dengan klik normal")
                            popup_ditutup = True
                            time.sleep(0.5)
                            return True
                        except:
                            pass
                        
                        # ✅ METHOD 2: JAVASCRIPT CLICK
                        try:
                            driver.execute_script("arguments[0].click();", popup)
                            if logger:
                                logger.info("✓ Popup ditutup dengan JavaScript")
                            popup_ditutup = True
                            time.sleep(0.5)
                            return True
                        except:
                            pass
                        
                        # ✅ METHOD 3: SEMBUNYIKAN
                        try:
                            driver.execute_script("""
                                var element = arguments[0];
                                element.style.display = 'none';
                                element.style.visibility = 'hidden';
                                element.style.opacity = '0';
                                
                                // Sembunyikan parent juga
                                var parent = element.parentNode;
                                if (parent) {
                                    parent.style.display = 'none';
                                }
                            """, popup)
                            if logger:
                                logger.info("✓ Popup disembunyikan dengan force hide")
                            popup_ditutup = True
                            time.sleep(0.5)
                            return True
                        except:
                            pass
                
            except:
                continue
        
        # ✅ JIKA TIDAK ADA POPUP SPESIFIK, COBA ESCAPE
        if not popup_ditutup:
            try:
                actions = ActionChains(driver)
                actions.send_keys(Keys.ESCAPE)
                actions.perform()
                time.sleep(0.2)
            except:
                pass
        
        if popup_ditutup:
            if logger:
                logger.info("✅ Popup cleanup selesai")
        else:
            if logger:
                logger.info("ℹ️ Tidak ada popup yang ditemukan")
        
        return popup_ditutup
        
    except Exception as e:
        if logger:
            logger.warning(f"⚠️ Error dalam cleanup_popups_once: {e}")
        return False


def click_body_javascript(driver, logger=None):
    """
    Klik body dengan JavaScript untuk memastikan fokus
    """
    try:
        if logger:
            logger.info("🖱️ Mengklik body dengan JavaScript...")
        
        # Script JavaScript untuk klik body
        click_script = """
        try {
            // Klik body
            if (document.body) {
                document.body.click();
                console.log('Body clicked successfully');
            }
            
            // Klik document juga untuk memastikan
            if (document.documentElement) {
                document.documentElement.click();
                console.log('Document element clicked successfully');
            }
            
            // Focus ke body
            if (document.body) {
                document.body.focus();
                console.log('Body focused successfully');
            }
            
            return true;
        } catch (error) {
            console.log('Error clicking body:', error);
            return false;
        }
        """
        
        result = driver.execute_script(click_script)
        
        if result:
            if logger:
                logger.info("✅ Body berhasil diklik dengan JavaScript")
                logger.info(f"{Y}{"─" *60}")
        else:
            if logger:
                logger.warning("⚠️ JavaScript click body mungkin gagal")
                logger.info(f"{Y}{"─" *60}")
        
        # Tunggu sebentar setelah klik
        time.sleep(random.uniform(0.5, 1))
        
        return True
        
    except Exception as e:
        if logger:
            logger.warning(f"⚠️ Error dalam click_body_javascript: {e}")
            logger.info(f"{Y}{"─" *60}")
        return False



def post_comment(driver, comment_data, comment_template, signature_data, bot_instance=None):
    """
    Post comment untuk Wix (Wix) dengan Google Sign-in - SIMPLIFIED
    """
    logger = bot_instance.logger if bot_instance else None
    
    try:
        if logger:
            logger.info("🚀 [Wix] Memulai proses posting comment...")
            logger.info(f"🎯 Target: {driver.current_url}")
        
        # Simpan URL asli untuk retry
        original_url = driver.current_url
        
        # TAHAP 1: Persiapan comment box
        success_prep = prepare_comment_box(driver, logger)
        if not success_prep:
            if logger:
                logger.error("❌ [Wix] Gagal mempersiapkan comment box")
            return False, driver.current_url
        
        if logger:
            logger.info("✅ [Wix] Persiapan comment box berhasil!")
            logger.info(f"{Y}{"─" *60}")
        
        # TAHAP 2: Klik login as member
        login_success = click_login_as_member(driver, logger)
        if not login_success:
            if logger:
                logger.error("❌ [Wix] Gagal klik login as member")
            return False, driver.current_url
        
        # if logger:
        #     logger.info("✅ [Wix] Login as member button berhasil diklik!")
        
        # TAHAP 3: Switch to signup
        signup_success = click_switch_to_signup(driver, logger)
        if not signup_success:
            if logger:
                logger.error("❌ [Wix] Gagal switch to signup")
            return False, driver.current_url
        
        if logger:
            # logger.info("✅ [Wix] Switch to signup berhasil diklik!")
            logger.info(f"{Y}{"─" *60}")
        
        # TAHAP 4: Klik tombol Google Sign-in
        if logger:
            logger.info("🔍 [Wix] Mencari tombol Google Sign-in...")
        
        google_signin_success = click_google_signin_button(driver, logger)
        if not google_signin_success:
            if logger:
                logger.error("❌ [Wix] Gagal klik tombol Google Sign-in")
            return False, driver.current_url
        
        # if logger:
        #     logger.info("✅ [Wix] Tombol Google Sign-in berhasil diklik!")
        
        # LANGSUNG HANDLE POPUP TANPA WAIT
        # if logger:
        #     logger.info("🔄 [Wix] Langsung handle popup...")
        
        # Load popups module secara dinamis
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            popups_path = os.path.join(current_dir, "popups.py")
            popups_module = load_module_from_path("popups", popups_path)
            
            if popups_module:
                # Handle popup dengan retry
                popup_success = popups_module.handle_popup_dengan_retry(driver, logger, max_retries=3)
                if popup_success:
                    if logger:
                        logger.info("✅ [Wix] Google login berhasil!")
                        logger.info(f"{Y}{"─" *60}")
                    
                    # ✅ TAMBAHAN: CEK AKUN TERKENA LIMIT
                    if logger:
                        logger.info("🔍 [Wix] Melakukan pengecekan status akun...")
                    
                    # Tunggu sebentar untuk halaman fully loaded
                    time.sleep(random.uniform(2, 4))
                    
                    # Cek apakah akun terkena limit
                    akun_limit = cek_akun_terkena_limit(driver, logger)
                    
                    if akun_limit:
                        if logger:
                            logger.error("🚫 [Wix] AKUN TERKENA LIMIT - Memindahkan akun...")
                        
                        # Baca akun dari akun.txt (2 baris pertama)
                        try:
                            if os.path.exists('akun.txt'):
                                with open('akun.txt', 'r', encoding='utf-8') as file:
                                    lines = [line.strip() for line in file if line.strip()]
                                
                                if len(lines) >= 2:
                                    email = lines[0]
                                    password = lines[1]
                                    
                                    # Pindahkan akun ke limit
                                    pindah_success = pindahkan_akun_ke_limit(email, password)
                                    
                                    if pindah_success:
                                        if logger:
                                            logger.info(f"✅ [Wix] Akun {email} berhasil dipindahkan ke akunlimit.txt")
                                    else:
                                        if logger:
                                            logger.error(f"❌ [Wix] Gagal memindahkan akun {email}")
                                else:
                                    if logger:
                                        logger.warning("⚠️ [Wix] File akun.txt tidak memiliki cukup data")
                            else:
                                if logger:
                                    logger.warning("⚠️ [Wix] File akun.txt tidak ditemukan")
                        except Exception as e:
                            if logger:
                                logger.error(f"❌ [Wix] Error saat membaca akun.txt: {e}")
                        
                        # ✅ TAMBAHAN: IMPORT DAN JALANKAN LOGOUT
                        try:
                            # Import fungsi logout dan pembersihan
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            logout_path = os.path.join(current_dir, "logout.py")
                            logout = load_module_from_path("logout", logout_path)
                            
                            if logout:
                                print(f"{G}{'='*50}")
                                print(f"{W}PEMBERSIHAN BROWSER SETELAH AKUN TERKENA LIMIT")
                                print(f"{G}{'='*50}{W}")
                                
                                # Lakukan logout dari Google terlebih dahulu
                                print(f"{Y}[{W}1/4{Y}] Logout dari Google...")
                                logout.logout_dari_google(driver)
                                
                                # Hapus semua cookies
                                print(f"{Y}[{W}2/4{Y}] Menghapus semua cookies...")
                                logout.hapus_cookies_menyeluruh(driver)
                                
                                # Hapus semua data browser
                                print(f"{Y}[{W}3/4{Y}] Menghapus semua data browser...")
                                logout.hapus_semua_data_browser(driver)
                                
                                # Reset browser state
                                print(f"{Y}[{W}4/4{Y}] Reset browser state...")
                                logout.reset_browser_state(driver)
                                
                                print(f"{G}✓ Pembersihan browser lengkap selesai")
                                
                                if logger:
                                    logger.info("✅ [Wix] Pembersihan browser setelah akun limit selesai")
                                
                                # ✅ TAMBAHAN: RETRY DENGAN AKUN LAIN
                                if logger:
                                    logger.info("🔄 [Wix] Mencoba login dengan akun lain...")
                                
                                # Cek apakah masih ada akun lain
                                if os.path.exists('akun.txt'):
                                    with open('akun.txt', 'r', encoding='utf-8') as file:
                                        remaining_lines = [line.strip() for line in file if line.strip()]
                                    
                                    if len(remaining_lines) >= 2:
                                        if logger:
                                            logger.info(f"🎯 [Wix] Masih ada {len(remaining_lines)//2} akun tersisa, mencoba akun berikutnya...")
                                        
                                        # Kembali ke URL asli
                                        driver.get(original_url)
                                        time.sleep(random.uniform(3, 5))
                                        
                                        # Recursive call untuk mencoba dengan akun baru
                                        return post_comment(driver, comment_data, comment_template, signature_data, bot_instance)
                                    else:
                                        if logger:
                                            logger.error("❌ [Wix] Tidak ada akun lain tersisa")
                                        return False, driver.current_url
                                else:
                                    if logger:
                                        logger.error("❌ [Wix] File akun.txt tidak ditemukan")
                                    return False, driver.current_url
                            else:
                                if logger:
                                    logger.warning("⚠️ [Wix] Modul logout tidak dapat dimuat")
                                print(f"{Y}Modul logout tidak tersedia, melakukan pembersihan sederhana...")
                                
                        except ImportError:
                            print(f"{Y}Modul logout tidak tersedia, melakukan pembersihan sederhana...")
                            if logger:
                                logger.warning("⚠️ [Wix] Import logout gagal, pembersihan sederhana")
                        except Exception as e:
                            print(f"{R}Error saat import logout: {W}{e}")
                            if logger:
                                logger.error(f"❌ [Wix] Error import logout: {e}")
                        
                        return False, driver.current_url
                    else:
                        if logger:
                            logger.info("✅ [Wix] Status akun normal - Melanjutkan proses...")

                else:
                    if logger:
                        logger.warning("⚠️ [Wix] Google login gagal, tapi lanjutkan...")
            else:
                if logger:
                    logger.error("❌ [Wix] Gagal load popups module")
                return False, driver.current_url
            
        except Exception as e:
            if logger:
                logger.error(f"❌ [Wix] Error handling Google popup: {e}")
            return False, driver.current_url
        
        # TAHAP 5: Lanjutkan ke proses komentar
        if logger:
            logger.info("🚀 [Wix] Melanjutkan ke proses komentar...")
        try:
            if logger:
                logger.info("🧹 [Wix] Membersihkan popup sekali...")
            
            # Pembersihan popup hanya 1 kali
            popup_cleaned = cleanup_popups_once(driver, logger)
            
            if popup_cleaned:
                if logger:
                    logger.info("✅ [Wix] Popup berhasil dibersihkan")
            else:
                if logger:
                    logger.info("ℹ️ [Wix] Tidak ada popup yang perlu dibersihkan")
            
            # Klik body dengan JavaScript
            if logger:
                # logger.info("🖱️ [Wix] Klik body dengan JavaScript...")
                logger.info("🖱️ [Wix] Klik body dengan click_safe_area...")
            
            # click_body_javascript(driver, logger)
                click_safe_area(driver, logger)
                logger.info(f"{Y}{"─" *60}")
            # Tunggu sebentar setelah pembersihan
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ [Wix] Error saat pembersihan popup: {e}")
        
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            komentar_path = os.path.join(current_dir, "komentar.py")
            komentar_module = load_module_from_path("komentar", komentar_path)
            
            if komentar_module:
                comment_success = komentar_module.lanjutkan_komentar(
                    driver, comment_data, comment_template, signature_data, logger
                )
                
                final_url = driver.current_url
                
                if comment_success:
                    if logger:
                        logger.info(f"🎉 [Wix] {G}Proses posting comment berhasil!")
                        logger.info(f"{Y}{"─" *60}")
                    return True, final_url
                else:
                    if logger:
                        logger.error(f"❌ [Wix] {R}Proses posting comment gagal")
                    return False, final_url
            else:
                if logger:
                    logger.error(f"❌ [Wix] {R}Gagal load komentar module")
                return False, driver.current_url
                
        except Exception as e:
            if logger:
                logger.error(f"❌ [Wix] {R}Error dalam proses komentar: {e}")
            return False, driver.current_url
        
    except Exception as e:
        if logger:
            logger.error(f"❌ [Wix] {R}Error dalam post_comment: {e}")
        return False, driver.current_url


def click_google_signin_button(driver, logger=None):
    """
    Klik tombol Google Sign-in dengan ID googleSM_ROOT_
    """
    try:
        # if logger:
        #     logger.info("🔍 Mencari tombol Google Sign-in...")
        
        # Selector untuk Google Sign-in button
        google_signin_selectors = [
            "#googleSM_ROOT_",
            "[id='googleSM_ROOT_']",
            "[id*='googleSM_ROOT_']",
            "[data-hook*='google']",
            "[data-testid*='google']",
            "button[id*='google' i]",
            "*[role='button'][id*='google' i]"
        ]
        
        for selector in google_signin_selectors:
            try:
                # if logger:
                #     logger.info(f"🔍 Mencoba selector: {selector}")
                
                element = driver.find_element(By.CSS_SELECTOR, selector)
                
                if element and element.is_displayed():
                    if logger:
                        logger.info(f"✅ {W}Google Sign-in button ditemukan: {Y}{selector}")
                    
                    # Scroll ke element
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    time.sleep(2)
                    
                    # Get element info
                    element_id = element.get_attribute("id") or "No ID"
                    element_text = element.text or "No text"
                    element_tag = element.tag_name
                    
                    if logger:
                        logger.info(f"🎯 {W}Google button info - Tag: {Y}{element_tag}{W}, ID: {Y}{element_id}{W}, Text: {Y}{element_text}")
                    
                    # Klik dengan berbagai metode
                    if click_element_with_methods(driver, element, "Google Sign-in button", logger):
                        # Tunggu sebentar untuk popup muncul
                        time.sleep(random.uniform(2, 4))
                        return True

                    
            except NoSuchElementException:
                continue
            except Exception as e:
                if logger:
                    logger.warning(f"⚠️ Error dengan selector {selector}: {e}")
                continue
        
        # Jika tidak ditemukan dengan selector spesifik, cari berdasarkan text
        try:
            if logger:
                logger.info("🔍 Mencari Google button berdasarkan text...")
            
            google_text_patterns = [
                "//button[contains(text(), 'Google')]",
                "//button[contains(text(), 'google')]",
                "//*[@role='button'][contains(text(), 'Google')]",
                "//*[contains(@class, 'google')]",
                "//*[contains(@id, 'google')]"
            ]
            
            for xpath in google_text_patterns:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
                        if logger:
                            logger.info(f"✅ Google button ditemukan via XPath: {xpath}")
                        
                        if click_element_with_methods(driver, element, "Google Sign-in button (XPath)", logger):
                            time.sleep(random.uniform(2, 4))
                            return True
                except:
                    continue
                    
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Error searching by text: {e}")
        
        if logger:
            logger.error(f"❌ Google Sign-in button tidak ditemukan")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error dalam click_google_signin_button: {e}")
        return False

# Fungsi-fungsi lainnya tetap sama
def prepare_comment_box(driver, logger=None):
    """
    Persiapan comment box dengan progress bar
    """
    try:
        if logger:
            logger.info(f"🚀 [Wix] Memulai persiapan comment box...")
            logger.info(f"{Y}{"─" *60}")

        
        # Step 1: Cari comment box
        if logger:
            logger.info(f"📍 Step 1: Mencari comment box dengan progress bar...")
        
        comment_box_found = find_comment_box_with_progress(driver, logger)
        if not comment_box_found:
            if logger:
                logger.error(f"❌ Comment box tidak ditemukan")
            return False
        
        # Step 2: Bersihkan popup
        if logger:
            logger.info(f"📍 Step 2: Membersihkan popup...")
        
        cleanup_popups(driver, logger)
        
        # Step 3: Abaikan popup yang mungkin muncul
        if logger:
            logger.info(f"📍 Step 3: Mengabaikan popup yang mungkin muncul...")
        
        time.sleep(random.uniform(1, 2))
        
        # Step 4: Klik area aman
        if logger:
            logger.info(f"📍 Step 4: Klik area aman...")
            
            click_safe_area(driver, logger)
        
        # Step 5: Klik comment box
        if logger:
            logger.info(f"📍 Step 5: Klik comment box...")
        
        comment_box_clicked = click_comment_box(driver, logger)
        if not comment_box_clicked:
            if logger:
                logger.warning("⚠️ Comment box tidak bisa diklik, tapi lanjutkan...")
        
        # if logger:
        #     logger.info("🎉 [Wix] Persiapan comment box selesai!")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error dalam prepare_comment_box: {e}")
        return False



def cleanup_popups(driver, logger=None):
    """
    Bersihkan popup yang menghalangi - MENGGUNAKAN TEKNIK YANG DIMINTA
    """
    try:
        # ✅ CARI POPUP SPESIFIK SESUAI PERMINTAAN
        popup_selectors = [
            'button#close.ng-scope',
            'button[id="close"][class="ng-scope"]',
            'button#close[aria-label="Close"]',
            '#close.ng-scope',
            # ✅ TAMBAHAN SELECTOR UMUM
            "[aria-label='Close']",
            "[aria-label='close']",
            ".close-button",
            ".close",
            "[data-hook='close-button']",
            "[data-testid='close-button']",
            ".modal-close",
            "[data-dismiss='modal']"
        ]
        
        popup_ditutup = False
        
        for selector in popup_selectors:
            try:
                popup_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                
                for popup in popup_elements:
                    if popup.is_displayed():
                        if logger:
                            logger.info(f"🚨 Popup ditemukan saat scroll: {selector}")
                        else:
                            print(f"{Y}🚨 Popup ditemukan saat scroll: {selector}{W}")
                        
                        # ✅ METHOD 1: KLIK LANGSUNG
                        try:
                            popup.click()
                            if logger:
                                logger.info("✓ Popup ditutup dengan klik normal")
                            else:
                                print(f"{G}✓ Popup ditutup dengan klik normal{W}")
                            popup_ditutup = True
                            time.sleep(0.5)
                            return True
                        except:
                            pass
                        
                        # ✅ METHOD 2: JAVASCRIPT CLICK
                        try:
                            driver.execute_script("arguments[0].click();", popup)
                            if logger:
                                logger.info("✓ Popup ditutup dengan JavaScript")
                            else:
                                print(f"{G}✓ Popup ditutup dengan JavaScript{W}")
                            popup_ditutup = True
                            time.sleep(0.5)
                            return True
                        except:
                            pass
                        
                        # ✅ METHOD 3: SEMBUNYIKAN
                        try:
                            driver.execute_script("""
                                var element = arguments[0];
                                element.style.display = 'none';
                                element.style.visibility = 'hidden';
                                element.style.opacity = '0';
                                
                                // Sembunyikan parent juga
                                var parent = element.parentNode;
                                if (parent) {
                                    parent.style.display = 'none';
                                }
                            """, popup)
                            if logger:
                                logger.info("✓ Popup disembunyikan dengan force hide")
                            else:
                                print(f"{G}✓ Popup disembunyikan dengan force hide{W}")
                            popup_ditutup = True
                            time.sleep(0.5)
                            return True
                        except:
                            pass
                
            except:
                continue
        
        # ✅ JIKA TIDAK ADA POPUP SPESIFIK, COBA ESCAPE
        if not popup_ditutup:
            try:
                actions = ActionChains(driver)
                actions.send_keys(Keys.ESCAPE)
                actions.perform()
                time.sleep(0.2)
            except:
                pass
        
        return popup_ditutup
        
    except Exception as e:
        if logger:
            logger.warning(f"Error saat tutup popup: {e}")
        else:
            print(f"{R}Error saat tutup popup: {e}{W}")
        return False


def find_comment_box_with_progress(driver, logger=None, timeout=600):
    try:
        if logger:
            logger.info("🧠 Smart Dynamic Scroll: Calculating optimal range...")
        else:
            print("🧠 Smart Dynamic Scroll: Calculating optimal range...")
        
        # ✅ GET ACTUAL PAGE HEIGHT
        page_height = driver.execute_script("return document.body.scrollHeight")
        
        # ✅ CALCULATE SMART RANGE  
        max_scroll = min(page_height * 1.2, 25000)
        scroll_step = 800
        total_steps = int(max_scroll // scroll_step)
        
        if logger:
            logger.info(f"📏 {W}Page height: {G}{page_height}{W}px")
            logger.info(f"🎯 {W}Smart max_scroll: {G}{max_scroll}{W}px")
            logger.info(f"📊 {W}Total steps: {G}{total_steps}")
        else:
            print(f"📏 {W}Page height: {G}{page_height}{W}px")
            print(f"🎯 {W}Smart max_scroll: {G}{max_scroll}{W}px")
            print(f"📊 {W}Total steps: {G}{total_steps}")
        
        start_time = time.time()
        scroll_position = 0
        popup_counter = 0
        current_step = 0
        
        while time.time() - start_time < timeout:
            try:
                # ✅ HITUNG PROGRESS PERCENTAGE
                progress_percentage = min(int((current_step / total_steps) * 100), 100) if total_steps > 0 else 0
                
                # ✅ BUAT PROGRESS BAR VISUAL
                bar_length = 20
                filled_length = int(bar_length * progress_percentage / 100)
                bar = '█' * filled_length + '░' * (bar_length - filled_length)
                
                # ✅ TAMPILKAN PROGRESS BAR TETAP DI SATU TEMPAT
                progress_text = f"🔋 {R}[{Y}{bar}{R}] {G}{progress_percentage}% {W}| 📍 {Y}Position: {G}{scroll_position}px {W}| {Y}Step {G}{current_step + 1}{W}/{G}{total_steps}"
                
                # ✅ HANYA GUNAKAN PRINT DENGAN \r, TIDAK LOGGER
                print(f"\r{G}{progress_text}{W}", end='', flush=True)
                
                # ✅ CLEANUP POPUP DENGAN TEKNIK YANG DIMINTA
                popup_found = cleanup_popups(driver, None)  # Tidak pass logger untuk menghindari output tambahan
                
                if popup_found:
                    popup_counter += 1
                    # Tampilkan popup info di baris baru sementara, lalu kembali ke progress
                    print(f"\n{Y}🗑️ Popup #{popup_counter} berhasil ditutup{W}")
                
                # ✅ SEARCH FOR ELEMENT
                elements = driver.find_elements(By.CSS_SELECTOR, "[id*='root-comment-box-start-']")
                
                for element in elements:
                    if element.is_displayed():
                        # ✅ TAMPILKAN PROGRESS BAR FINAL (100%)
                        final_bar = '█' * bar_length
                        final_text = f"🔋 {Y}[{G}{final_bar}{Y}] {W}100% {Y}| ✅ {W}Element found at position: {G}{scroll_position}px"
                        
                        # Clear line dan tampilkan hasil final
                        print(f"\r{G}{final_text}{W}")
                        if popup_counter > 0:
                            print(f"\n{Y}📊 Total popup ditutup selama scroll: {popup_counter}{W}")
                        # print()  # Baris kosong untuk pemisah
                        
                        # Log ke logger jika ada (untuk file log)
                        # if logger:
                        #     logger.info(f"✅ Element found at position: {scroll_position}px")
                        #     if popup_counter > 0:
                        #         logger.info(f"📊 Total popup ditutup selama scroll: {popup_counter}")
                        
                        # ✅ FINAL CLEANUP SEBELUM SCROLL KE ELEMENT
                        final_popup = cleanup_popups(driver, None)
                        if final_popup:
                            popup_counter += 1
                            print(f"{Y}🗑️ Final popup ditutup sebelum scroll ke element{W}")
                        
                        # Scroll ke element
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                        time.sleep(2)
                        
                        # ✅ CLEANUP POPUP SETELAH SCROLL KE ELEMENT
                        after_scroll_popup = cleanup_popups(driver, None)
                        if after_scroll_popup:
                            popup_counter += 1
                        #     print(f"{Y}🗑️ Popup ditutup setelah scroll ke element{W}")
                        
                        #  print(f"{G}🎯 Element berhasil ditemukan! Total popup ditutup: {popup_counter}{W}")
                        
                        # if logger:
                        #     logger.info(f"🎯 Element berhasil ditemukan! Total popup ditutup: {popup_counter}")
                        
                        return True
                
                # ✅ SCROLL LOGIC
                if scroll_position < max_scroll:
                    # Scroll ke posisi berikutnya
                    driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                    scroll_position += scroll_step
                    current_step += 1
                    
                    # ✅ DELAY UNTUK POPUP MUNCUL
                    time.sleep(0.8)
                    
                else:
                    # ✅ RESET SCROLL
                    new_page_height = driver.execute_script("return document.body.scrollHeight")
                    if new_page_height > page_height:
                        page_height = new_page_height
                        max_scroll = min(page_height * 1.2, 25000)
                        total_steps = int(max_scroll // scroll_step)
                        print(f"\n{Y}📈 Page height updated: {page_height}px → max_scroll: {max_scroll}px{W}")
                        if logger:
                            logger.info(f"📈 Page height updated: {page_height}px → max_scroll: {max_scroll}px")
                    
                    # Cleanup sebelum reset
                    cleanup_popups(driver, None)
                    
                    # Reset progress
                    print(f"\n{Y}🔄 Resetting scroll position...{W}")
                    if logger:
                        logger.info("🔄 Resetting scroll position...")
                    
                    driver.execute_script("window.scrollTo(0, 0);")
                    scroll_position = 0
                    current_step = 0
                    time.sleep(1.5)
                    
            except Exception as e:
                print(f"\n{R}⚠️ Error in smart scroll at position {scroll_position}px: {e}{W}")
                if logger:
                    logger.warning(f"⚠️ Error in smart scroll at position {scroll_position}px: {e}")
                
                # ✅ CLEANUP POPUP SAAT ERROR
                try:
                    cleanup_popups(driver, None)
                except:
                    pass
                
                time.sleep(1)
        
        # ✅ TAMPILKAN PROGRESS BAR TIMEOUT
        timeout_bar = '░' * bar_length
        timeout_text = f"🔋 [{timeout_bar}] TIMEOUT | ❌ Element not found with smart dynamic scroll"
        
        print(f"\r{R}{timeout_text}{W}")
        print(f"\n{Y}📊 Summary: Total popup ditutup selama pencarian: {popup_counter}{W}")
        print()  # Baris kosong untuk pemisah
        
        if logger:
            logger.error("❌ Timeout: Element not found with smart dynamic scroll")
            logger.info(f"📊 Summary: Total popup ditutup selama pencarian: {popup_counter}")
        
        return False
        
    except Exception as e:
        print(f"\n{R}❌ Error in smart dynamic scroll: {e}{W}")
        if logger:
            logger.error(f"❌ Error in smart dynamic scroll: {e}")
        
        # ✅ FINAL CLEANUP
        try:
            cleanup_popups(driver, None)
        except:
            pass
        
        return False




def tutup_popup_saat_scroll(driver):
    """
    Fungsi untuk menutup popup yang muncul saat scrolling atau sebelum klik elemen
    """
    popup_yang_ditutup = []
    
    # Daftar selector popup yang umum ditemukan
    popup_selectors = [
        "button#close.ng-scope",
        "button[id*='close']",
        "button.close",
        ".close",
        "[class*='close']",
        ".dismiss",
        "[class*='dismiss']",
        ".fa-times",
        ".icon-close",
        "[aria-label='Close']",
        "[title='Close']",
        "[id*='close']",
        "[id*='dismiss']",
        ".modal-backdrop",
        ".overlay",
        ".popup-overlay",
        "[data-dismiss='modal']",
        ".modal-close",
        "button[class*='close']"
    ]
    
    for selector in popup_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    try:
                        # Method 1: Klik normal
                        element.click()
                        popup_yang_ditutup.append(f"Normal click: {selector}")
                        time.sleep(0.3)
                    except:
                        try:
                            # Method 2: JavaScript click
                            driver.execute_script("arguments[0].click();", element)
                            popup_yang_ditutup.append(f"JS click: {selector}")
                            time.sleep(0.3)
                        except:
                            try:
                                # Method 3: Force hide dengan CSS
                                driver.execute_script("arguments[0].style.display = 'none';", element)
                                popup_yang_ditutup.append(f"Force hide: {selector}")
                                time.sleep(0.3)
                            except:
                                pass
        except:
            continue
    
    # Tekan Escape sebagai langkah tambahan
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE)
        actions.perform()
        time.sleep(0.2)
    except:
        pass
    
    return len(popup_yang_ditutup) > 0


def click_safe_area(driver, logger=None):
    """
    Fungsi khusus untuk mengklik body dan menghilangkan popup sebelum klik elemen komentar
    ✅ DENGAN PENGECEKAN NEW TAB DAN URL PROTECTION - ULTRA SAFE VERSION
    """
    try:
        # ✅ SIMPAN URL AWAL
        initial_url = driver.current_url
        
        # ✅ SIMPAN WINDOW/TAB AWAL
        initial_windows = driver.window_handles
        initial_window_count = len(initial_windows)
        main_window = driver.current_window_handle
        
        if logger:
            logger.info(f"🖱️ [SafeClick] Mengklik body untuk menghilangkan popup...")
            logger.info(f"📊 [SafeClick] Initial window count: {initial_window_count}")
            logger.info(f"🌐 [SafeClick] Initial URL: {initial_url}")
        
        # Method 1: ULTRA-SAFE Body + Margin Browser Click ONLY
        driver.execute_script("""
            // 1. ✅ Body click (AMAN)
            if (document.body) {
                document.body.click();
                console.log('✅ Body diklik untuk menghilangkan popup');
            }
            
            // 2. ✅ HANYA margin browser yang BENAR-BENAR aman
            var ultraSafeAreas = [
                // Margin browser (3px dari edge) - PALING AMAN
                {x: 3, y: 3, name: 'Pojok kiri atas margin'},                                           
                {x: window.innerWidth - 3, y: 3, name: 'Pojok kanan atas margin'},                      
                {x: 3, y: window.innerHeight - 3, name: 'Pojok kiri bawah margin'},                     
                {x: window.innerWidth - 3, y: window.innerHeight - 3, name: 'Pojok kanan bawah margin'}, 
                
                // Margin tengah edge (tidak ada elemen HTML di sini)
                {x: 2, y: window.innerHeight / 2, name: 'Edge kiri tengah'},                     
                {x: window.innerWidth - 2, y: window.innerHeight / 2, name: 'Edge kanan tengah'}, 
                {x: window.innerWidth / 2, y: 2, name: 'Edge atas tengah'},                      
                {x: window.innerWidth / 2, y: window.innerHeight - 2, name: 'Edge bawah tengah'}  
            ];
            
            console.log('🛡️ Mengklik HANYA area margin ultra-safe (8 titik)...');
            
            var successfulClicks = 0;
            var skippedClicks = 0;
            
            ultraSafeAreas.forEach(function(area, index) {
                try {
                    var elementAtPoint = document.elementFromPoint(area.x, area.y);
                    
                    // VALIDASI KETAT: Hanya body atau html
                    if (elementAtPoint && 
                        (elementAtPoint.tagName === 'BODY' || 
                         elementAtPoint.tagName === 'HTML')) {
                        
                        var ultraSafeEvent = new MouseEvent('click', {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: area.x,
                            clientY: area.y
                        });
                        
                        elementAtPoint.dispatchEvent(ultraSafeEvent);
                        successfulClicks++;
                        console.log('✅ Ultra-safe #' + (index + 1) + ' (' + area.name + ') clicked at: [' + area.x + ', ' + area.y + '] - Element: ' + elementAtPoint.tagName);
                        
                        // Small delay between ultra-safe clicks
                        setTimeout(function() {}, 30);
                        
                    } else {
                        skippedClicks++;
                        console.log('⚠️ Ultra-safe #' + (index + 1) + ' (' + area.name + ') SKIPPED - Element: ' + (elementAtPoint ? elementAtPoint.tagName + ' (not body/html)' : 'null'));
                    }
                } catch(e) {
                    skippedClicks++;
                    console.log('❌ Error clicking ultra-safe #' + (index + 1) + ' (' + area.name + '):', e);
                }
            });
            
            // 3. ✅ Focus ke body (AMAN)
            if (document.body) {
                document.body.focus();
                console.log('✅ Body focused successfully');
            }
            
            // 4. ✅ Summary ultra-safe clicks
            console.log('📊 Ultra-safe click summary:');
            console.log('   ✅ Successful clicks: ' + successfulClicks + '/8');
            console.log('   ⚠️ Skipped clicks: ' + skippedClicks + '/8');
            console.log('   🛡️ Total safe operations: ' + (successfulClicks + 2) + ' (including body click & focus)');
            
            console.log('🎯 Method 1: ULTRA-SAFE margin-only clicks completed');
        """)
        
        if logger:
            logger.info(f"✅ [SafeClick] Method 1: ULTRA-SAFE Body + Margin Browser clicks completed")
        
        time.sleep(1)
        
        # ✅ CEK URL SETELAH METHOD 1 (ULTRA-SAFE CLICKS)
        current_url_after_js = driver.current_url
        if current_url_after_js != initial_url:
            if logger:
                logger.warning(f"🚨 [SafeClick] URL berubah setelah Method 1 (Ultra-Safe)!")
                logger.warning(f"🔄 [SafeClick] URL awal: {initial_url}")
                logger.warning(f"🔄 [SafeClick] URL sekarang: {current_url_after_js}")
                logger.info(f"🔙 [SafeClick] Mengembalikan ke URL awal...")
            
            # Kembali ke URL awal
            driver.get(initial_url)
            time.sleep(2)
            
            if logger:
                logger.info(f"✅ [SafeClick] URL berhasil dikembalikan ke: {driver.current_url}")
        
        # ✅ CEK APAKAH ADA TAB BARU SETELAH METHOD 1
        current_windows_after_js = driver.window_handles
        if len(current_windows_after_js) > initial_window_count:
            if logger:
                logger.warning(f"🚨 [SafeClick] Tab baru terdeteksi setelah Method 1 (Ultra-Safe)!")
            
            close_new_tabs(driver, initial_windows, main_window, logger)
        
        # Method 2: Klik dengan ActionChains di area aman
        try:
            actions = ActionChains(driver)
            # ✅ ULTRA-SAFE: Klik di margin browser saja (bukan content area)
            actions.move_by_offset(5, 5)  # Margin kiri atas
            actions.click()
            actions.perform()
            
            # ✅ CEK URL SETELAH ACTIONCHAINS CLICK
            time.sleep(0.5)
            current_url_after_action = driver.current_url
            if current_url_after_action != initial_url:
                if logger:
                    logger.warning(f"🚨 [SafeClick] URL berubah setelah ActionChains click!")
                    logger.warning(f"🔄 [SafeClick] URL awal: {initial_url}")
                    logger.warning(f"🔄 [SafeClick] URL sekarang: {current_url_after_action}")
                    logger.info(f"🔙 [SafeClick] Mengembalikan ke URL awal...")
                
                # Kembali ke URL awal
                driver.get(initial_url)
                time.sleep(2)
                
                if logger:
                    logger.info(f"✅ [SafeClick] URL berhasil dikembalikan ke: {driver.current_url}")
            
            # ✅ CEK TAB BARU SETELAH ACTIONCHAINS CLICK
            current_windows_after_action = driver.window_handles
            if len(current_windows_after_action) > len(current_windows_after_js):
                if logger:
                    logger.warning(f"🚨 [SafeClick] Tab baru terdeteksi setelah ActionChains click!")
                
                close_new_tabs(driver, initial_windows, main_window, logger)
            
            # Reset mouse position ke margin
            actions.move_by_offset(-5, -5)
            actions.perform()
            
            if logger:
                logger.info(f"✅ [SafeClick] Ultra-safe margin berhasil diklik dengan ActionChains")
            
            time.sleep(0.5)
            
        except Exception as action_error:
            if logger:
                logger.warning(f"⚠️ [SafeClick] ActionChains click gagal: {action_error}")
        
        # Method 3: Klik pada elemen body secara langsung
        try:
            body_element = driver.find_element(By.TAG_NAME, "body")
            body_element.click()
            
            # ✅ CEK URL SETELAH BODY ELEMENT CLICK
            time.sleep(0.5)
            current_url_after_body = driver.current_url
            if current_url_after_body != initial_url:
                if logger:
                    logger.warning(f"🚨 [SafeClick] URL berubah setelah body element click!")
                    logger.warning(f"🔄 [SafeClick] URL awal: {initial_url}")
                    logger.warning(f"🔄 [SafeClick] URL sekarang: {current_url_after_body}")
                    logger.info(f"🔙 [SafeClick] Mengembalikan ke URL awal...")
                
                # Kembali ke URL awal
                driver.get(initial_url)
                time.sleep(2)
                
                if logger:
                    logger.info(f"✅ [SafeClick] URL berhasil dikembalikan ke: {driver.current_url}")
            
            # ✅ CEK TAB BARU SETELAH BODY ELEMENT CLICK
            current_windows_after_body = driver.window_handles
            if len(current_windows_after_body) > initial_window_count:
                if logger:
                    logger.warning(f"🚨 [SafeClick] Tab baru terdeteksi setelah body element click!")
                
                close_new_tabs(driver, initial_windows, main_window, logger)
            
            if logger:
                logger.info(f"✅ [SafeClick] Body element berhasil diklik langsung")
            
            time.sleep(0.5)
            
        except Exception as body_error:
            if logger:
                logger.warning(f"⚠️ [SafeClick] Body element click gagal: {body_error}")
        
        # Tutup popup yang mungkin masih ada
        if logger:
            logger.info(f"🧹 [SafeClick] Memeriksa dan menutup popup yang tersisa...")
        
        for i in range(2):  # Coba 2 kali
            if tutup_popup_saat_scroll(driver):
                if logger:
                    logger.info(f"✅ [SafeClick] Popup berhasil ditutup (percobaan {i+1})")
                time.sleep(0.5)
        
        # Tekan Escape sebagai langkah tambahan
        try:
            if logger:
                logger.info(f"🔑 [SafeClick] Menekan Escape key untuk memastikan popup hilang...")
            
            actions = ActionChains(driver)
            actions.send_keys(Keys.ESCAPE)
            actions.perform()
            
            if logger:
                logger.info(f"✅ [SafeClick] Escape key berhasil ditekan")
            
            time.sleep(1)
            
        except Exception as escape_error:
            if logger:
                logger.warning(f"⚠️ [SafeClick] Escape key gagal: {escape_error}")
        
        # ✅ FINAL CHECK: Pastikan tidak ada tab baru yang tersisa
        final_windows = driver.window_handles
        if len(final_windows) > initial_window_count:
            if logger:
                logger.warning(f"🚨 [SafeClick] Final check: Masih ada tab baru yang tersisa!")
            
            close_new_tabs(driver, initial_windows, main_window, logger)
        
        # ✅ PASTIKAN KEMBALI KE MAIN WINDOW
        if driver.current_window_handle != main_window:
            driver.switch_to.window(main_window)
            if logger:
                logger.info(f"🔄 [SafeClick] Switched back to main window")
        
        # ✅ FINAL URL CHECK
        final_url = driver.current_url
        if final_url != initial_url:
            if logger:
                logger.warning(f"🚨 [SafeClick] Final check: URL masih berbeda!")
                logger.warning(f"🔄 [SafeClick] URL awal: {initial_url}")
                logger.warning(f"🔄 [SafeClick] URL final: {final_url}")
                logger.info(f"🔙 [SafeClick] Melakukan final redirect ke URL awal...")
            
            # Final redirect ke URL awal
            driver.get(initial_url)
            time.sleep(2)
            
            if logger:
                logger.info(f"✅ [SafeClick] Final URL check: {driver.current_url}")
        
        if logger:
            logger.info(f"✅ [SafeClick] Proses pembersihan popup dan tab selesai")
            logger.info(f"📊 [SafeClick] Final window count: {len(driver.window_handles)}")
            logger.info(f"🌐 [SafeClick] Final URL: {driver.current_url}")
        
        # ✅ RETURN STATUS URL
        return driver.current_url == initial_url
        
    except Exception as click_error:
        if logger:
            logger.error(f"❌ [SafeClick] Gagal mengklik body: {click_error}")
        return False



def close_new_tabs(driver, initial_windows, main_window, logger=None):
    """
    ✅ FUNGSI BARU: Tutup semua tab baru yang muncul
    """
    try:
        current_windows = driver.window_handles
        new_tabs_count = 0
        
        if logger:
            logger.info(f"🔍 [TabClose] Checking for new tabs...")
            logger.info(f"📊 [TabClose] Initial: {len(initial_windows)}, Current: {len(current_windows)}")
        
        # Cari dan tutup tab baru
        for window_handle in current_windows:
            if window_handle not in initial_windows:
                try:
                    # Switch ke tab baru
                    driver.switch_to.window(window_handle)
                    new_tabs_count += 1
                    
                    # Get info tab baru
                    try:
                        tab_url = driver.current_url
                        tab_title = driver.title
                        if logger:
                            logger.warning(f"🗑️ [TabClose] Closing new tab #{new_tabs_count}")
                            logger.warning(f"📄 [TabClose] URL: {tab_url}")
                            logger.warning(f"📄 [TabClose] Title: {tab_title}")
                    except:
                        if logger:
                            logger.warning(f"🗑️ [TabClose] Closing new tab #{new_tabs_count} (info unavailable)")
                    
                    # Tutup tab
                    driver.close()
                    
                    if logger:
                        logger.info(f"✅ [TabClose] Tab #{new_tabs_count} berhasil ditutup")
                    
                except Exception as e:
                    if logger:
                        logger.error(f"❌ [TabClose] Error closing tab: {e}")
        
        # Kembali ke main window
        try:
            driver.switch_to.window(main_window)
            if logger:
                logger.info(f"🔄 [TabClose] Switched back to main window")
        except Exception as e:
            # Jika main window tidak ada, ambil window pertama yang tersisa
            remaining_windows = driver.window_handles
            if remaining_windows:
                driver.switch_to.window(remaining_windows[0])
                if logger:
                    logger.warning(f"⚠️ [TabClose] Main window unavailable, switched to first available window")
            else:
                if logger:
                    logger.error(f"❌ [TabClose] No windows available!")
        
        if new_tabs_count > 0:
            if logger:
                logger.info(f"🎯 [TabClose] Summary: {new_tabs_count} new tab(s) closed")
        else:
            if logger:
                logger.info(f"ℹ️ [TabClose] No new tabs found")
        
        return new_tabs_count
        
    except Exception as e:
        if logger:
            logger.error(f"❌ [TabClose] Error in close_new_tabs: {e}")
        return 0


def detect_new_tab_triggers(driver, logger=None):
    """
    ✅ FUNGSI BARU: Deteksi elemen yang mungkin membuka tab baru
    """
    try:
        if logger:
            logger.info(f"🔍 [TabDetect] Scanning for potential new tab triggers...")
        
        # Selector elemen yang sering membuka tab baru
        risky_selectors = [
            'a[target="_blank"]',           # Link dengan target blank
            'a[href*="http"]:not([href*="' + driver.current_url.split('/')[2] + '"])',  # External links
            '[onclick*="window.open"]',     # JavaScript window.open
            '[onclick*="target"]',          # Target dalam onclick
            'a[href*="facebook.com"]',      # Social media links
            'a[href*="twitter.com"]',
            'a[href*="instagram.com"]',
            'a[href*="youtube.com"]',
            'a[href*="linkedin.com"]',
            '.social-link',                 # Social link classes
            '.external-link',               # External link classes
            '[class*="share"]',             # Share buttons
            '[class*="social"]'             # Social buttons
        ]
        
        risky_elements = []
        
        for selector in risky_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        risky_elements.append({
                            'selector': selector,
                            'element': element,
                            'text': element.text[:50] if element.text else 'No text',
                            'href': element.get_attribute('href') if element.tag_name == 'a' else 'N/A'
                        })
            except:
                continue
        
        if risky_elements and logger:
            logger.warning(f"⚠️ [TabDetect] Found {len(risky_elements)} potential new tab triggers:")
            for i, elem in enumerate(risky_elements[:5]):  # Show first 5
                logger.warning(f"   {i+1}. {elem['selector']} - Text: {elem['text']} - Href: {elem['href']}")
            
            if len(risky_elements) > 5:
                logger.warning(f"   ... and {len(risky_elements) - 5} more")
        
        return risky_elements
        
    except Exception as e:
        if logger:
            logger.error(f"❌ [TabDetect] Error detecting new tab triggers: {e}")
        return []


def safe_click_with_tab_protection(driver, element, element_name="element", logger=None):
    """
    ✅ FUNGSI BARU: Safe click dengan proteksi tab baru
    """
    try:
        # Simpan state awal
        initial_windows = driver.window_handles
        initial_window_count = len(initial_windows)
        main_window = driver.current_window_handle
        
        if logger:
            logger.info(f"🖱️ [SafeClick] Clicking {element_name} with tab protection...")
        
        # Lakukan click
        element.click()
        
        # Tunggu sebentar untuk tab baru muncul
        time.sleep(1)
        
        # Cek apakah ada tab baru
        current_windows = driver.window_handles
        if len(current_windows) > initial_window_count:
            if logger:
                logger.warning(f"🚨 [SafeClick] New tab detected after clicking {element_name}!")
            
            tabs_closed = close_new_tabs(driver, initial_windows, main_window, logger)
            
            if logger:
                logger.info(f"✅ [SafeClick] {tabs_closed} new tab(s) closed, continuing...")
        
        return True
        
    except Exception as e:
        if logger:
            logger.error(f"❌ [SafeClick] Error in safe_click_with_tab_protection: {e}")
        return False




def click_comment_box(driver, logger=None):
    """
    Klik comment box dengan berbagai metode
    """
    try:
        if logger:
            # logger.info("🖱️ Mencoba klik comment box...")
        
            # Selector untuk comment box
            comment_box_selector = "[id*='root-comment-box-start-']"
        
        try:
            element = driver.find_element(By.CSS_SELECTOR, comment_box_selector)
            
            if element and element.is_displayed():
                # Method 1: Direct Click
                try:
                    if logger:
                        # logger.info("🖱️ Mencoba Direct Click...")
                    
                        element.click()
                        time.sleep(random.uniform(1, 2))
                    
                    # if logger:
                    #     logger.info("✅ Comment box berhasil diklik dengan Direct Click!")
                    
                    return True
                    
                except ElementClickInterceptedException:
                    if logger:
                        logger.warning("⚠️ Direct click terhalang, mencoba metode lain...")
                except Exception as e:
                    if logger:
                        logger.warning(f"⚠️ Direct click gagal: {e}")
                
                # Method 2: JavaScript Click
                try:
                    if logger:
                        logger.info("🖱️ Mencoba JavaScript Click...")
                    
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(random.uniform(1, 2))
                    
                    if logger:
                        logger.info("✅ Comment box berhasil diklik dengan JavaScript!")
                    
                    return True
                    
                except Exception as e:
                    if logger:
                        logger.warning(f"⚠️ JavaScript click gagal: {e}")
                
                # Method 3: ActionChains
                try:
                    if logger:
                        logger.info("🖱️ Mencoba ActionChains...")
                    
                    actions = ActionChains(driver)
                    actions.move_to_element(element).click().perform()
                    time.sleep(random.uniform(1, 2))
                    
                    if logger:
                        logger.info("✅ Comment box berhasil diklik dengan ActionChains!")
                    
                    return True
                    
                except Exception as e:
                    if logger:
                        logger.warning(f"⚠️ ActionChains gagal: {e}")
            else:
                if logger:
                    logger.error("❌ Comment box element tidak ditemukan atau tidak visible")
        
        except NoSuchElementException:
            if logger:
                logger.error("❌ Comment box element tidak ditemukan di DOM")
        except Exception as e:
            if logger:
                logger.error(f"❌ Error mencari comment box element: {e}")
        
        if logger:
            logger.error("❌ Semua metode klik comment box gagal")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error dalam click_comment_box: {e}")
        return False

def click_login_as_member(driver, logger=None):
    """
    Klik login as member button
    """
    try:
        # if logger:
        #     logger.info("🔍 Mencari login-as-member button...")
        
        # Selector untuk login button
        login_selectors = [
            "[data-hook='login-as-member-text-button']",
            "[data-testid='login-as-member']",
            "button[data-hook*='login']",
            "*[role='button'][data-hook*='login']"
        ]
        
        for selector in login_selectors:
            try:
                if logger:
                    logger.info(f"🔍{W}Mencoba selector: {Y}{selector}")
                
                element = driver.find_element(By.CSS_SELECTOR, selector)
                
                if element and element.is_displayed():
                    if logger:
                        logger.info(f"✅ {W}Login button ditemukan dengan CSS selector: {Y}{selector}")
                    
                    # Scroll ke element
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    time.sleep(2)
                    
                    # Get button info
                    button_text = element.text or "No text"
                    button_tag = element.tag_name
                    
                    if logger:
                        logger.info(f"🎯 {W}Button info - Tag: {Y}{button_tag}, {W}Text: {Y}{button_text}")
                    
                    # Klik dengan berbagai metode
                    if click_element_with_methods(driver, element, "login button", logger):
                        return True
                    
            except NoSuchElementException:
                continue
            except Exception as e:
                if logger:
                    logger.warning(f"⚠️ Error dengan selector {selector}: {e}")
                continue
        
        if logger:
            logger.error("❌ Login button tidak ditemukan")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error dalam click_login_as_member: {e}")
        return False

def click_switch_to_signup(driver, logger=None):
    """
    Klik switch to signup element
    """
    try:
        if logger:
            logger.info("🔍 Mencari switch to signup element...")
        
        # Selector untuk signup element
        signup_selectors = [
            "[data-testid='switchToSignUp']",
            "[data-hook='switchToSignUp']",
            "button[data-testid*='signup']",
            "*[role='button'][data-testid*='signup']"
        ]
        
        for selector in signup_selectors:
            try:
                if logger:
                    logger.info(f"🔍 Mencoba selector: {Y}{selector}")
                
                element = driver.find_element(By.CSS_SELECTOR, selector)
                
                if element and element.is_displayed():
                    if logger:
                        logger.info(f"✅ Signup element ditemukan dengan CSS selector: {Y}{selector}")
                    
                    # Scroll ke element
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    time.sleep(2)
                    
                    # Get element info
                    element_text = element.text or "No text"
                    element_tag = element.tag_name
                    element_testid = element.get_attribute("data-testid") or "No testid"
                    
                    if logger:
                        logger.info(f"🎯 {W}Signup element info - Tag: {Y}{element_tag}{W}, Text: {Y}{element_text}{W}, TestID: {Y}{element_testid}")
                    # Klik dengan berbagai metode
                    if click_element_with_methods(driver, element, "signup element", logger):
                        return True
                    
            except NoSuchElementException:
                continue
            except Exception as e:
                if logger:
                    logger.warning(f"⚠️ Error dengan selector {selector}: {e}")
                continue
        
        if logger:
            logger.error("❌ Signup element tidak ditemukan")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error dalam click_switch_to_signup: {e}")
        return False

def click_element_with_methods(driver, element, element_name, logger=None):
    """
    Klik element dengan berbagai metode
    """
    try:
        # Method 1: Direct Click
        try:
            if logger:
                # logger.info(f"🖱️ Mencoba Direct Click pada {element_name}...")

                #    # 1. Simpan window handle utama sebelum klik
                # main_window = driver.current_window_handles[0]
            
                element.click()
                time.sleep(random.uniform(1, 2))

                # popup_window = [w for w in driver.window_handles if w != main_window][0]
                #     # 4. Switch ke popup dan atur ukuran
                # driver.switch_to.window(popup_window)
                # driver.set_window_size(500, 600)  # Atur ukuran popup
                # driver.set_window_position(0, 0) 
            
            if logger:
                logger.info(f"✅ {G}{element_name} berhasil diklik dengan Direct Click!")
            
            return True
            
        except ElementClickInterceptedException:
            if logger:
                logger.warning(f"⚠️ Direct click {element_name} terhalang, mencoba metode lain...")
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Direct click {element_name} gagal: {e}")
        
        # Method 2: JavaScript Click
        try:
            if logger:
                logger.info(f"🖱️ Mencoba JavaScript Click pada {element_name}...")
            
            driver.execute_script("arguments[0].click();", element)
            time.sleep(random.uniform(1, 2))
            
            if logger:
                logger.info(f"✅ {element_name} berhasil diklik dengan JavaScript!")
            
            return True
            
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ JavaScript click {element_name} gagal: {e}")
        
        # Method 3: ActionChains
        try:
            if logger:
                logger.info(f"🖱️ Mencoba ActionChains pada {element_name}...")
            
            actions = ActionChains(driver)
            actions.move_to_element(element).click().perform()
            time.sleep(random.uniform(1, 2))
            
            if logger:
                logger.info(f"✅ {element_name} berhasil diklik dengan ActionChains!")
            
            return True
            
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ ActionChains {element_name} gagal: {e}")
        
        # Method 4: Force Click dengan koordinat
        try:
            if logger:
                logger.info(f"🖱️ Mencoba Force Click pada {element_name}...")
            
            # Get element location dan size
            location = element.location
            size = element.size
            
            # Klik di tengah element
            center_x = location['x'] + size['width'] // 2
            center_y = location['y'] + size['height'] // 2
            
            actions = ActionChains(driver)
            actions.move_by_offset(center_x, center_y).click().perform()
            time.sleep(random.uniform(1, 2))
            
            if logger:
                logger.info(f"✅ {element_name} berhasil diklik dengan Force Click!")
            
            return True
            
        except Exception as e:
            if logger:
                logger.warning(f"⚠️ Force click {element_name} gagal: {e}")
        
        if logger:
            logger.error(f"❌ Semua metode klik {element_name} gagal")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error dalam click_element_with_methods untuk {element_name}: {e}")
        return False



def wait_for_google_popup(driver, logger=None, timeout=15):
    """
    Tunggu popup Google muncul setelah klik googleSM_ROOT_
    """
    try:
        if logger:
            logger.info("⏳ Menunggu popup Google muncul...")
        
        start_time = time.time()
        initial_windows = driver.window_handles
        initial_window_count = len(initial_windows)
        
        if logger:
            logger.info(f"📊 Window count awal: {initial_window_count}")
        
        # Loop menunggu popup muncul
        while time.time() - start_time < timeout:
            try:
                current_windows = driver.window_handles
                current_window_count = len(current_windows)
                
                # Cek apakah ada window baru
                if current_window_count > initial_window_count:
                    if logger:
                        logger.info(f"🪟 Popup terdeteksi! Window count: {initial_window_count} → {current_window_count}")
                    
                    # Cek apakah popup adalah Google
                    new_window = None
                    for window in current_windows:
                        if window not in initial_windows:
                            new_window = window
                            break
                    
                    if new_window:
                        # Switch ke popup untuk verifikasi
                        main_window = driver.current_window_handle
                        driver.switch_to.window(new_window)
                        
                        # Cek URL popup
                        popup_url = driver.current_url
                        if logger:
                            logger.info(f"🔍 Popup URL: {popup_url}")
                        
                        # Verifikasi ini adalah popup Google
                        if is_google_popup(driver, popup_url, logger):
                            if logger:
                                logger.info("✅ Popup Google terverifikasi!")
                            
                            # Kembali ke main window
                            driver.switch_to.window(main_window)
                            return True
                        else:
                            if logger:
                                logger.warning("⚠️ Popup bukan Google, tutup dan tunggu lagi...")
                            
                            # Tutup popup yang bukan Google
                            driver.close()
                            driver.switch_to.window(main_window)
                
                # Tunggu sebentar sebelum cek lagi
                time.sleep(0.5)
                
            except Exception as e:
                if logger:
                    logger.warning(f"⚠️ Error saat menunggu popup: {e}")
                time.sleep(0.5)
        
        if logger:
            logger.error(f"❌ Timeout: Popup Google tidak muncul dalam {timeout} detik")
        return False
        
    except Exception as e:
        if logger:
            logger.error(f"❌ Error dalam wait_for_google_popup: {e}")
        return False

def is_google_popup(driver, popup_url, logger=None):
    """
    Verifikasi apakah popup adalah popup Google
    """
    try:
        # Cek URL
        google_indicators = [
            'accounts.google.com',
            'google.com/accounts',
            'oauth.google.com',
            'accounts.youtube.com'
        ]
        
        url_is_google = any(indicator in popup_url.lower() for indicator in google_indicators)
        
        if url_is_google:
            if logger:
                logger.info(f"✅ URL adalah Google: {popup_url}")
            return True
        
        # Cek title halaman
        try:
            page_title = driver.title.lower()
            title_indicators = ['google', 'sign in', 'login']
            
            title_is_google = any(indicator in page_title for indicator in title_indicators)
            
            if title_is_google:
                if logger:
                    logger.info(f"✅ Title adalah Google: {driver.title}")
                return True
        except:
            pass
        
        # Cek elemen Google di halaman
        try:
            google_elements = [
                "[data-provider-id='google']",
                "#identifierId",
                "input[type='email'][id*='identifier']",
                ".google-logo",
                "[aria-label*='Google']"
            ]
            
            for selector in google_elements:
                if driver.find_elements(By.CSS_SELECTOR, selector):
                    if logger:
                        logger.info(f"✅ Element Google ditemukan: {selector}")
                    return True
        except:
            pass
        
        if logger:
            logger.warning(f"❌ Bukan popup Google: {popup_url}")
        return False
        
    except Exception as e:
        if logger:
            logger.warning(f"⚠️ Error verifying Google popup: {e}")
        return False
