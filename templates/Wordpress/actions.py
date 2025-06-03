import time
import random
import os
import sys
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
from colorama import Fore, init


# Initialize Colorama
init(autoreset=True)

# Colors for terminal text
B = Fore.BLUE
W = Fore.WHITE
R = Fore.RED
G = Fore.GREEN
Y = Fore.YELLOW


current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from smart_detection import SmartSuccessDetector
    SMART_DETECTION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Smart detection not available: {e}")
    SMART_DETECTION_AVAILABLE = False

def close_popups_once(driver, bot_instance):
    """Tutup popup sekali saja - jika muncul lagi akan diabaikan"""
    popup_selectors = [
        '.modal', '.popup', '.overlay', '.lightbox',
        '.newsletter-popup', '.email-popup', '.subscribe-popup',
        '.cookie-banner', '.cookie-consent', '#cookie-notice',
        '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]',
        '[class*="newsletter"]', '[class*="subscribe"]', '[class*="cookie"]'
    ]
    
    closed_count = 0
    for selector in popup_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                if element.is_displayed():
                    try:
                        # Coba hide dengan JavaScript
                        driver.execute_script("arguments[0].style.display = 'none';", element)
                        closed_count += 1
                    except:
                        continue
        except:
            continue
    
    if closed_count > 0:
        bot_instance.logger.info(f"🚫 Menutup {closed_count} popup")
    
    return closed_count

def scroll_and_find_comment_form(driver, bot_instance, target_selectors, max_wait_time=180):
    """Scroll sambil mencari comment form - abaikan popup yang muncul lagi"""
    domain = driver.current_url.split('/')[2].lower()
    bot_instance.logger.info(f"🔍 Scroll mencari comment form...")
    
    # Variabel tracking
    last_height = 0
    scroll_attempts = 0
    max_scroll_attempts = 20
    wait_start_time = None
    element_search_interval = 2
    last_search_time = 0
    
    while True:
        current_time = time.time()
        
        # Cari element setiap interval
        if current_time - last_search_time >= element_search_interval:
            for selector in target_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            # Clear loading bar dan tampilkan hasil
                            print(f"\r{'█' * 20} 100% ✅ {G}Comment form ditemukan", end="")
                            print()  # New line untuk log berikutnya
                            bot_instance.logger.info(f"✅ {W}Comment form ditemukan: {Y}{selector}")
                            return element, selector
                except:
                    continue
            
            last_search_time = current_time
        
        # Cek tinggi halaman
        current_height = driver.execute_script("return document.body.scrollHeight")
        
        # Jika masih bisa scroll
        if current_height > last_height and scroll_attempts < max_scroll_attempts:
            wait_start_time = None
            
            # Update loading bar untuk scrolling
            progress = (scroll_attempts + 1) / max_scroll_attempts
            filled_length = int(20 * progress)
            bar = '█' * filled_length + '░' * (20 - filled_length)
            percent = int(100 * progress)
            print(f"\r📜 Scrolling: {bar} {percent}%", end="", flush=True)
            
            # Scroll ke bawah
            scroll_position = driver.execute_script("return window.pageYOffset")
            scroll_step = random.randint(300, 800)
            
            driver.execute_script(f"window.scrollTo(0, {scroll_position + scroll_step});")
            
            last_height = current_height
            scroll_attempts += 1
            
            time.sleep(random.uniform(1.5, 3.0))
            
        else:
            # Tidak bisa scroll lagi, mulai waiting
            if wait_start_time is None:
                wait_start_time = current_time
                # Update ke waiting mode di line yang sama
                print(f"\r⏳ Waiting: {'░' * 20} 0% (sisa {max_wait_time/60:.1f}m)", end="", flush=True)
            
            # Cek timeout
            elapsed_wait = current_time - wait_start_time
            if elapsed_wait >= max_wait_time:
                print(f"\r⏰ Timeout: {'█' * 20} 100% - tidak ditemukan", end="")
                print()  # New line
                bot_instance.logger.warning(f"⏰ Timeout - comment form tidak ditemukan")
                return None, None
            
            # Update loading bar untuk waiting di line yang sama
            wait_progress = elapsed_wait / max_wait_time
            filled_length = int(20 * wait_progress)
            bar = '█' * filled_length + '░' * (20 - filled_length)
            percent = int(100 * wait_progress)
            remaining_minutes = (max_wait_time - elapsed_wait) / 60
            print(f"\r⏳ Waiting: {bar} {percent}% (sisa {remaining_minutes:.1f}m)", end="", flush=True)
            
            time.sleep(1)
    
    return None, None

def check_popup_after_form_found(driver, bot_instance):
    """Cek popup setelah form ditemukan - tutup sekali, jika muncul lagi abaikan"""
    bot_instance.logger.info("🔍 Cek popup setelah form ditemukan...")
    
    time.sleep(1)  # Tunggu popup muncul
    
    popup_selectors = [
        '.modal', '.popup', '.overlay',
        '[class*="modal"]', '[class*="popup"]', '[class*="overlay"]'
    ]
    
    popup_found = False
    for selector in popup_selectors:
        try:
            popups = driver.find_elements(By.CSS_SELECTOR, selector)
            for popup in popups:
                if popup.is_displayed():
                    popup_found = True
                    bot_instance.logger.info(f"🚨 Popup ditemukan: {selector}")
                    
                    try:
                        # Tutup dengan JavaScript
                        driver.execute_script("arguments[0].style.display = 'none';", popup)
                        bot_instance.logger.info("✅ Popup ditutup")
                    except:
                        bot_instance.logger.info("⚠️ Popup tidak bisa ditutup - akan diabaikan")
                    
                    break
        except:
            continue
    
    if not popup_found:
        bot_instance.logger.info("✅ Tidak ada popup")


def click_empty_area(driver, bot_instance):
    """
    Click di area kosong yang tidak ada link
    ✅ DENGAN NEW TAB PROTECTION & AUTO-CLOSE
    """
    bot_instance.logger.info("🎯 Click di area kosong...")
    
    try:
        # ✅ SIMPAN STATE AWAL
        initial_windows = driver.window_handles
        initial_window_count = len(initial_windows)
        main_window = driver.current_window_handle
        initial_url = driver.current_url
        
        bot_instance.logger.info(f"📊 [EmptyClick] Initial state - Windows: {initial_window_count}, URL: {initial_url}")
        
        # Strategy 1: Click di body dengan koordinat aman + NEW TAB PROTECTION
        window_size = driver.get_window_size()
        width = window_size['width']
        height = window_size['height']
        
        # Koordinat yang biasanya aman (tidak ada link) - ULTRA SAFE
        safe_coordinates = [
            (width // 8, height // 12),      # Kiri atas aman
            (width // 6, height // 10),      # Kiri atas dalam
            (width // 10, height // 8),      # Kiri tengah atas
            (width - 50, 30),                # Kanan atas margin
            (30, height - 50),               # Kiri bawah margin
            (width - 30, height - 30)        # Kanan bawah margin
        ]
        
        successful_clicks = 0
        new_tabs_detected = 0
        
        for i, (safe_x, safe_y) in enumerate(safe_coordinates):
            try:
                bot_instance.logger.info(f"🖱️ [EmptyClick] Attempt #{i+1}: Clicking safe area ({safe_x}, {safe_y})")
                
                # ✅ SIMPAN WINDOW STATE SEBELUM CLICK
                windows_before_click = driver.window_handles
                
                # Click menggunakan JavaScript untuk memastikan tidak ada link
                click_result = driver.execute_script(f"""
                    var x = {safe_x};
                    var y = {safe_y};
                    var element = document.elementFromPoint(x, y);
                    
                    // Pastikan bukan link, button, atau elemen interaktif
                    if (element && 
                        element.tagName !== 'A' && 
                        element.tagName !== 'BUTTON' && 
                        element.tagName !== 'INPUT' &&
                        !element.closest('a') &&
                        !element.closest('button') &&
                        !element.closest('[role="button"]') &&
                        !element.closest('.social-share') &&
                        !element.closest('.external-link')) {{
                        
                        var event = new MouseEvent('click', {{
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: x,
                            clientY: y
                        }});
                        element.dispatchEvent(event);
                        
                        return {{
                            success: true,
                            elementTag: element.tagName,
                            elementClass: element.className || 'no-class'
                        }};
                    }} else {{
                        return {{
                            success: false,
                            reason: element ? 'Interactive element detected: ' + element.tagName : 'No element found',
                            elementTag: element ? element.tagName : 'null'
                        }};
                    }}
                """)
                
                if click_result and click_result.get('success'):
                    successful_clicks += 1
                    bot_instance.logger.info(f"✅ {Y}[{W}EmptyClick{W}] Click #{i+1} {G}successful {W}on {G}{click_result.get('elementTag', 'unknown')} element")
                    
                    # ✅ TUNGGU SEBENTAR UNTUK NEW TAB MUNCUL
                    time.sleep(0.5)
                    
                    # ✅ CEK NEW TAB SETELAH CLICK
                    windows_after_click = driver.window_handles
                    
                    if len(windows_after_click) > len(windows_before_click):
                        new_tabs_count = len(windows_after_click) - len(windows_before_click)
                        new_tabs_detected += new_tabs_count
                        
                        bot_instance.logger.warning(f"🚨 [EmptyClick] NEW TAB DETECTED after click #{i+1}! Count: {new_tabs_count}")
                        
                        # ✅ TUTUP NEW TABS
                        tabs_closed = close_new_tabs_wordpress(driver, windows_before_click, main_window, bot_instance.logger, f"EmptyClick-{i+1}")
                        
                        bot_instance.logger.info(f"🗑️ [EmptyClick] {tabs_closed} new tab(s) closed after click #{i+1}")
                        
                        # ✅ CEK URL SETELAH CLOSE TABS
                        current_url = driver.current_url
                        if current_url != initial_url:
                            bot_instance.logger.warning(f"🚨 [EmptyClick] URL changed after click #{i+1}!")
                            bot_instance.logger.warning(f"🔄 [EmptyClick] Original: {initial_url}")
                            bot_instance.logger.warning(f"🔄 [EmptyClick] Current: {current_url}")
                            
                            # Restore URL
                            driver.get(initial_url)
                            time.sleep(1)
                            bot_instance.logger.info(f"✅ [EmptyClick] URL restored to: {driver.current_url}")
                    
                else:
                    bot_instance.logger.warning(f"⚠️ [EmptyClick] Click #{i+1} skipped: {click_result.get('reason', 'Unknown reason')}")
                
                # Small delay between clicks
                time.sleep(random.uniform(0.3, 0.7))
                
            except Exception as e:
                bot_instance.logger.warning(f"⚠️ [EmptyClick] Error in click #{i+1}: {str(e)}")
                continue
        
        # ✅ FINAL CHECK & CLEANUP
        final_windows = driver.window_handles
        if len(final_windows) > initial_window_count:
            remaining_new_tabs = len(final_windows) - initial_window_count
            bot_instance.logger.warning(f"🚨 [EmptyClick] Final check: {remaining_new_tabs} new tab(s) still open!")
            
            final_tabs_closed = close_new_tabs_wordpress(driver, initial_windows, main_window, bot_instance.logger, "FinalCleanup")
            bot_instance.logger.info(f"🗑️ [EmptyClick] Final cleanup: {final_tabs_closed} tab(s) closed")
        
        # ✅ ENSURE MAIN WINDOW FOCUS
        if driver.current_window_handle != main_window:
            try:
                driver.switch_to.window(main_window)
                bot_instance.logger.info(f"🔄 [EmptyClick] Switched back to main window")
            except:
                # If main window is gone, use first available
                available_windows = driver.window_handles
                if available_windows:
                    driver.switch_to.window(available_windows[0])
                    bot_instance.logger.warning(f"⚠️ [EmptyClick] Main window gone, switched to first available")
        
        # ✅ SUMMARY LOG
        bot_instance.logger.info(f"📊 [EmptyClick] Summary:")
        bot_instance.logger.info(f"   ✅ Successful clicks: {successful_clicks}/{len(safe_coordinates)}")
        bot_instance.logger.info(f"   🚨 New tabs detected: {new_tabs_detected}")
        bot_instance.logger.info(f"   🗑️ All new tabs closed: {'Yes' if len(driver.window_handles) == initial_window_count else 'No'}")
        bot_instance.logger.info(f"   🌐 URL stable: {'Yes' if driver.current_url == initial_url else 'No'}")
        bot_instance.logger.info(f"   📍 Final URL: {driver.current_url}")
        bot_instance.logger.info(f"{Y}{"─" *60}")
        return True
        
    except Exception as e:
        bot_instance.logger.error(f"❌ Error click area kosong: {str(e)}")
        
        # ✅ EMERGENCY CLEANUP
        try:
            current_windows = driver.window_handles
            if len(current_windows) > 1:
                emergency_closed = close_new_tabs_wordpress(driver, [current_windows[0]], current_windows[0], bot_instance.logger, "Emergency")
                bot_instance.logger.info(f"🚨 [EmptyClick] Emergency cleanup: {emergency_closed} tab(s) closed")
        except:
            pass
        
        return False


def close_new_tabs_wordpress(driver, initial_windows, main_window, logger, context=""):
    """
    ✅ FUNGSI BARU: Tutup semua tab baru yang muncul (WordPress specific)
    """
    try:
        current_windows = driver.window_handles
        new_tabs_closed = 0
        
        if logger:
            logger.info(f"🔍 [{context}] Checking for new tabs...")
            logger.info(f"📊 [{context}] Initial: {len(initial_windows)}, Current: {len(current_windows)}")
        
        # Cari dan tutup tab baru
        for window_handle in current_windows:
            if window_handle not in initial_windows:
                try:
                    # Switch ke tab baru
                    driver.switch_to.window(window_handle)
                    new_tabs_closed += 1
                    
                    # Get info tab baru
                    try:
                        tab_url = driver.current_url
                        tab_title = driver.title[:50] if driver.title else "No title"
                        if logger:
                            logger.warning(f"🗑️ [{context}] Closing new tab #{new_tabs_closed}")
                            logger.warning(f"📄 [{context}] URL: {tab_url}")
                            logger.warning(f"📄 [{context}] Title: {tab_title}")
                    except:
                        if logger:
                            logger.warning(f"🗑️ [{context}] Closing new tab #{new_tabs_closed} (info unavailable)")
                    
                    # Tutup tab
                    driver.close()
                    
                    if logger:
                        logger.info(f"✅ [{context}] Tab #{new_tabs_closed} berhasil ditutup")
                    
                except Exception as e:
                    if logger:
                        logger.error(f"❌ [{context}] Error closing tab: {e}")
        
        # Kembali ke main window
        try:
            driver.switch_to.window(main_window)
            if logger:
                logger.info(f"🔄 [{context}] Switched back to main window")
        except Exception as e:
            # Jika main window tidak ada, ambil window pertama yang tersisa
            remaining_windows = driver.window_handles
            if remaining_windows:
                driver.switch_to.window(remaining_windows[0])
                if logger:
                    logger.warning(f"⚠️ [{context}] Main window unavailable, switched to first available window")
            else:
                if logger:
                    logger.error(f"❌ [{context}] No windows available!")
        
        if new_tabs_closed > 0:
            if logger:
                logger.info(f"🎯 [{context}] Summary: {new_tabs_closed} new tab(s) closed")
        else:
            if logger:
                logger.info(f"ℹ️ [{context}] No new tabs found")
        
        return new_tabs_closed
        
    except Exception as e:
        if logger:
            logger.error(f"❌ [{context}] Error in close_new_tabs_wordpress: {e}")
        return 0



def post_comment(driver, comment_data, comment_template, signature_data, bot_instance):
    """Post comment dengan smart detection"""
    try:
        domain = driver.current_url.split('/')[2].lower()
        original_url = driver.current_url
        bot_instance.logger.info(f"🚀 {W}Memulai posting comment di {Y}{domain}")
        bot_instance.logger.info(f"📍 {W}Original URL: {Y}{original_url}")
        
        # Step 1: Tutup popup di awal
        close_popups_once(driver, bot_instance)
        time.sleep(2)
        
        # Step 2: Scroll dan cari comment form
        comment_selectors = [
            '#commentform', '#comment-form', '.comment-form',
            '#respond form', '.comment-respond form',
            'form[action*="comment"]', 'form[id*="comment"]', 'form[class*="comment"]',
            'form[action*="reply"]', 'form[id*="reply"]',
            '#disqus_thread', '.disqus-comment-form',
            '.post-comment-form', '.add-comment-form', '.reply-form',
            '[class*="comment-form"]', '[id*="comment-form"]'
        ]
        
        comment_form, used_selector = scroll_and_find_comment_form(
            driver, bot_instance, comment_selectors, max_wait_time=180
        )
        
        if not comment_form:
            bot_instance.logger.error("❌ Comment form tidak ditemukan")
            return False, original_url
        
        # Step 3: Cek popup setelah form ditemukan
        check_popup_after_form_found(driver, bot_instance)
        
        # Step 4: Click di area kosong
        click_empty_area(driver, bot_instance)
        
        # Step 5: Scroll ke form dan isi dengan smart detection
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", comment_form)
        time.sleep(2)
        
        # ✅ PANGGIL DENGAN SMART DETECTION
        success, final_url = fill_comment_form(
            driver,
            comment_form, 
            comment_data, 
            comment_template, 
            signature_data, 
            bot_instance
        )
        
        if success:
            bot_instance.logger.info(f"✅ {G}Comment berhasil dipost dengan smart detection")
            bot_instance.logger.info(f"🎯 {W}Final URL: {G}{final_url}")
            bot_instance.logger.info(f"{Y}{"─" *60}")
            return True, final_url
        else:
            bot_instance.logger.error("❌ Comment gagal dipost")
            return False, original_url
            
    except Exception as e:
        bot_instance.logger.error(f"❌ Error posting comment: {str(e)}")
        return False, driver.current_url

def find_form_field_with_cache(form_element, field_keywords, bot_instance, element_type):
    """Cari field dalam form dengan element caching"""
    try:
        # Get domain untuk caching
        domain = urlparse(bot_instance.driver.current_url).netloc.lower()
        
        # ✅ CEK CACHE DULU
        cached_selector = bot_instance.get_cached_selector(domain, element_type)
        if cached_selector:
            try:
                field = form_element.find_element(By.CSS_SELECTOR, cached_selector)
                if field.is_displayed():
                    bot_instance.logger.info(f"🚀 {W}Using cached selector for {element_type}: {Y}{cached_selector}")
                    bot_instance.logger.info(f"{Y}{"─" *60}")
                    return field
                    
                else:
                    bot_instance.logger.info(f"⚠️ Cached selector not visible, searching new one")
            except Exception as e:
                bot_instance.logger.info(f"⚠️ Cached selector failed: {e}")
        
        # ✅ SEARCH NEW SELECTOR
        bot_instance.logger.info(f"🔍 Searching {element_type} with keywords: {field_keywords}")
        
        for keyword in field_keywords:
            selectors = [
                f'input[name*="{keyword}"]',
                f'input[id*="{keyword}"]',
                f'textarea[name*="{keyword}"]',
                f'textarea[id*="{keyword}"]',
                f'input[placeholder*="{keyword}" i]',
                f'textarea[placeholder*="{keyword}" i]'
            ]
            
            for selector in selectors:
                try:
                    field = form_element.find_element(By.CSS_SELECTOR, selector)
                    if field.is_displayed():
                        # ✅ CACHE SELECTOR YANG BERHASIL
                        bot_instance.cache_selector(domain, element_type, selector)
                        bot_instance.logger.info(f"✅ Found and cached {element_type}: {selector}")
                        return field
                except:
                    continue
        
        bot_instance.logger.warning(f"❌ {element_type} not found with keywords: {field_keywords}")
        return None
        
    except Exception as e:
        bot_instance.logger.error(f"❌ Error finding {element_type}: {e}")
        return None

def fill_comment_form(driver, form_element, comment_data, comment_template, signature_data, bot_instance):
    """Fill form dengan element caching"""
    try:
        original_url = driver.current_url
        bot_instance.logger.info(f"📍 URL awal: {Y}{original_url}")
        
        # ✅ SMART DETECTION SETUP
        use_smart_detection = False
        smart_detector = None
        
        try:
            current_dir = os.path.dirname(__file__)
            sys.path.insert(0, current_dir)
            
            from smart_detection import SmartSuccessDetector
            smart_detector = SmartSuccessDetector(bot_instance)
            before_state = smart_detector.capture_page_state(driver)
            bot_instance.logger.info("📸 Captured before-submit state")
            use_smart_detection = True
            
        except ImportError as e:
            bot_instance.logger.warning(f"⚠️ Smart detection not available: {e}")
            use_smart_detection = False
        except Exception as e:
            bot_instance.logger.warning(f"⚠️ Smart detector init failed: {e}")
            use_smart_detection = False
        
        # ✅ FIND FIELDS WITH CACHING
        name_field = find_form_field_with_cache(
            form_element, ['name', 'author'], bot_instance, 'name_field'
        )
        email_field = find_form_field_with_cache(
            form_element, ['email', 'mail'], bot_instance, 'email_field'
        )
        website_field = find_form_field_with_cache(
            form_element, ['website', 'url', 'site'], bot_instance, 'website_field'
        )
        comment_field = find_form_field_with_cache(
            form_element, ['comment', 'message', 'content'], bot_instance, 'comment_field'
        )
        
        if not comment_field:
            bot_instance.logger.error("❌ Comment field tidak ditemukan")
            return False, original_url
        
        # ✅ ISI FIELDS
        if name_field:
            type_human_like(name_field, comment_data['name'])
            bot_instance.logger.info("✅ Nama diisi")
        
        if email_field:
            type_human_like(email_field, comment_data['email'])
            bot_instance.logger.info("✅ Email diisi")
        
        if website_field:
            type_human_like(website_field, comment_data['website'])
            bot_instance.logger.info("✅ Website diisi")
        
        # Isi comment
        final_comment = comment_template or comment_data['comment']
        type_human_like(comment_field, final_comment)
        bot_instance.logger.info("✅ Comment diisi")
        
        # ✅ SUBMIT FORM DENGAN CACHE
        time.sleep(random.uniform(2, 4))
        submit_success = try_submit_with_cache(driver, form_element, bot_instance)
        
        if submit_success:
            bot_instance.logger.info(f"✅ {G}Form berhasil disubmit")
            bot_instance.logger.info(f"{G}{"─" *60}")
            
            # Smart detection
            if use_smart_detection and smart_detector:
                try:
                    is_success, detection_data = smart_detector.detect_success(driver, before_state, wait_time=5)
                    final_url = driver.current_url
                    
                    if is_success:
                        bot_instance.logger.info("🎯 SMART DETECTION: Comment submission SUCCESS")
                        bot_instance.logger.info(f"📊 Detection confidence: {detection_data.get('confidence', 0)}%")
                    else:
                        bot_instance.logger.warning("⚠️ SMART DETECTION: Comment submission UNCERTAIN")
                        is_success = True
                    
                    return is_success, final_url
                except Exception as e:
                    bot_instance.logger.warning(f"⚠️ Smart detection error: {e}")
                    time.sleep(5)
                    return True, driver.current_url
            else:
                time.sleep(5)
                return True, driver.current_url
        else:
            bot_instance.logger.error("❌ Submit button gagal")
            return False, original_url
        
    except Exception as e:
        bot_instance.logger.error(f"❌ Error mengisi form: {str(e)}")
        return False, driver.current_url

def wait_and_capture_final_url(driver, original_url, bot_instance, max_wait=15):
    """Tunggu redirect dan capture URL final"""
    try:
        bot_instance.logger.info("⏳ Menunggu redirect/reload...")
        
        start_time = time.time()
        last_url = original_url
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            current_url = driver.current_url
            
            # Cek apakah URL berubah
            if current_url != last_url:
                bot_instance.logger.info(f"🔄 URL berubah: {current_url}")
                last_url = current_url
                stable_count = 0
            else:
                stable_count += 1
            
            # Jika URL stabil selama 3 detik, anggap selesai
            if stable_count >= 3:
                bot_instance.logger.info(f"✅ URL stabil: {current_url}")
                break
                
            # Cek indikator success
            if check_comment_success_indicators(driver, bot_instance):
                bot_instance.logger.info("✅ Success indicator ditemukan")
                break
                
            time.sleep(1)
        
        final_url = driver.current_url
        
        # Log perubahan URL
        if final_url != original_url:
            bot_instance.logger.info(f"🎯 URL BERUBAH: {original_url} → {final_url}")
        else:
            bot_instance.logger.info(f"📍 URL TETAP: {final_url}")
            
        return final_url
        
    except Exception as e:
        bot_instance.logger.warning(f"⚠️ Error capturing final URL: {e}")
        return driver.current_url

def check_comment_success_indicators(driver, bot_instance):
    """Cek indikator bahwa komentar berhasil dipost"""
    try:
        # Success indicators
        success_selectors = [
            ".comment-success",
            ".success-message", 
            ".comment-submitted",
            ".awaiting-moderation",
            ".comment-pending",
            ".thank-you",
            "[class*='success']",
            "[class*='submitted']",
            "[class*='pending']"
        ]
        
        for selector in success_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        bot_instance.logger.info(f"✅ Success indicator: {selector}")
                        return True
            except:
                continue
        
        # Cek text indicators
        page_source = driver.page_source.lower()
        success_texts = [
            "comment submitted",
            "awaiting moderation", 
            "comment pending",
            "thank you",
            "successfully posted",
            "comment received"
        ]
        
        for text in success_texts:
            if text in page_source:
                bot_instance.logger.info(f"✅ Success text: {text}")
                return True
                
        return False
        
    except Exception as e:
        bot_instance.logger.warning(f"⚠️ Error checking success indicators: {e}")
        return False

def get_submit_selectors(bot_instance):
    """Get submit button selectors"""
    try:
        return [
            'input[type="submit"]',
            'button[type="submit"]', 
            'button[name="submit"]',
            'input[name="submit"]',
            'button[id*="submit"]',
            'input[id*="submit"]',
            '.submit-button',
            '#submit'
        ]
    except Exception as e:
        bot_instance.logger.warning(f"⚠️ Error getting submit selectors: {e}")
        return ['input[type="submit"]']

def find_submit_button_with_cache(form_element, bot_instance):
    """Cari submit button dengan caching"""
    try:
        domain = urlparse(bot_instance.driver.current_url).netloc.lower()
        
        # ✅ CEK CACHE DULU
        cached_selector = bot_instance.get_cached_selector(domain, 'submit_button')
        if cached_selector:
            try:
                submit_button = form_element.find_element(By.CSS_SELECTOR, cached_selector)
                if submit_button.is_displayed() and submit_button.is_enabled():
                    bot_instance.logger.info(f"🚀 Using cached submit button: {cached_selector}")
                    return submit_button, cached_selector
                else:
                    bot_instance.logger.info(f"⚠️ Cached submit button not available")
            except Exception as e:
                bot_instance.logger.info(f"⚠️ Cached submit button failed: {e}")
        
        # ✅ SEARCH NEW SUBMIT BUTTON
        bot_instance.logger.info("🔍 Searching submit button...")
        
        submit_selectors = [
            'input[type="submit"]',
            'button[type="submit"]', 
            'button[name="submit"]',
            'input[name="submit"]',
            'button[id*="submit"]',
            'input[id*="submit"]',
            '.submit-button',
            '#submit',
            'button[class*="submit"]',
            'input[class*="submit"]',
            'button[value*="submit" i]',
            'input[value*="submit" i]',
            'button[value*="post" i]',
            'input[value*="post" i]',
            'button[value*="send" i]',
            'input[value*="send" i]'
        ]
        
        for selector in submit_selectors:
            try:
                submit_button = form_element.find_element(By.CSS_SELECTOR, selector)
                if submit_button.is_displayed() and submit_button.is_enabled():
                    # ✅ CACHE SELECTOR YANG BERHASIL
                    bot_instance.cache_selector(domain, 'submit_button', selector)
                    bot_instance.logger.info(f"✅ Found and cached submit button: {selector}")
                    return submit_button, selector
            except:
                continue
        
        bot_instance.logger.warning("❌ Submit button tidak ditemukan")
        return None, None
        
    except Exception as e:
        bot_instance.logger.error(f"❌ Error finding submit button: {e}")
        return None, None

def try_submit_with_cache(driver, form_element, bot_instance):
    """Submit form dengan caching"""
    try:
        # ✅ GUNAKAN CACHED SUBMIT BUTTON
        submit_button, used_selector = find_submit_button_with_cache(form_element, bot_instance)
        
        if submit_button:
            bot_instance.logger.info(f"🎯 Menggunakan submit button: {used_selector}")
            
            # Scroll ke button
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
            time.sleep(1)
            
            # Click button
            submit_button.click()
            bot_instance.logger.info("✅ Submit button berhasil diklik")
            return True
        
        # ✅ FALLBACK: Submit form langsung
        bot_instance.logger.info("🔄 Fallback: Submit form langsung...")
        form_element.submit()
        bot_instance.logger.info("✅ Form submit langsung berhasil")
        return True
        
    except Exception as e:
        bot_instance.logger.error(f"❌ Submit gagal: {str(e)}")
        return False

def find_form_field(form_element, field_keywords):
    """Cari field dalam form"""
    for keyword in field_keywords:
        selectors = [
            f'input[name*="{keyword}"]',
            f'input[id*="{keyword}"]',
            f'textarea[name*="{keyword}"]',
            f'textarea[id*="{keyword}"]'
        ]
        
        for selector in selectors:
            try:
                field = form_element.find_element(By.CSS_SELECTOR, selector)
                if field.is_displayed():
                    return field
            except:
                continue
    
    return None

def type_human_like(element, text):
    """Ketik seperti manusia"""
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))