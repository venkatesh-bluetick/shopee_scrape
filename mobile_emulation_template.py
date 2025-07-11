#!/usr/bin/env python3
"""
Mobile Browser Emulation Template for Shopee Scraping
Using Android Emulator + ADB Network Capture + Mobile Chrome
"""

import subprocess
import time
import json
import threading
import queue
import re
from datetime import datetime
from typing import Dict, List, Optional

class AndroidEmulatorManager:
    """Manages Android emulator instances for mobile scraping"""
    
    def __init__(self, emulator_name: str = "shopee_scraper"):
        self.emulator_name = emulator_name
        self.adb_path = "adb"  # Adjust path as needed
        self.emulator_path = "emulator"  # Adjust path as needed
        self.is_running = False
        
    def start_emulator(self) -> bool:
        """Start Android emulator with network monitoring configuration"""
        try:
            # Start emulator in background
            cmd = [
                self.emulator_path,
                "-avd", self.emulator_name,
                "-no-audio",
                "-no-window",  # Headless mode
                "-gpu", "off",
                "-netdelay", "none",
                "-netspeed", "full",
                "-port", "5554"
            ]
            
            print(f"Starting emulator: {self.emulator_name}")
            self.emulator_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Wait for emulator to boot
            self._wait_for_emulator_boot()
            self.is_running = True
            return True
            
        except Exception as e:
            print(f"Error starting emulator: {e}")
            return False
    
    def _wait_for_emulator_boot(self, timeout: int = 120):
        """Wait for emulator to complete boot process"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    [self.adb_path, "-s", "emulator-5554", "shell", "getprop", "sys.boot_completed"],
                    capture_output=True, text=True, timeout=10
                )
                
                if result.returncode == 0 and "1" in result.stdout:
                    print("Emulator boot completed")
                    time.sleep(5)  # Additional wait for stability
                    return True
                    
            except subprocess.TimeoutExpired:
                pass
                
            time.sleep(2)
        
        raise Exception("Emulator boot timeout")
    
    def stop_emulator(self):
        """Stop the emulator instance"""
        if hasattr(self, 'emulator_process'):
            self.emulator_process.terminate()
            self.is_running = False
            print("Emulator stopped")

class MobileChromeManager:
    """Manages mobile Chrome browser sessions within Android emulator"""
    
    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path
        self.device_id = "emulator-5554"
        self.chrome_package = "com.android.chrome"
        
    def setup_mobile_chrome_session(self) -> bool:
        """Initialize authenticated mobile Chrome session"""
        try:
            # Clear Chrome data for fresh session
            self._clear_chrome_data()
            
            # Start Chrome browser
            self._start_chrome()
            
            # Navigate to Shopee login
            self._navigate_to_shopee_login()
            
            # Wait for manual login (or implement automated login)
            print("Please complete login manually in the emulator...")
            input("Press Enter after login is complete...")
            
            # Verify login success
            return self._verify_login_status()
            
        except Exception as e:
            print(f"Error setting up Chrome session: {e}")
            return False
    
    def _clear_chrome_data(self):
        """Clear Chrome browser data"""
        subprocess.run([
            self.adb_path, "-s", self.device_id, "shell", "pm", "clear", self.chrome_package
        ])
        print("Chrome data cleared")
    
    def _start_chrome(self):
        """Start Chrome browser on emulator"""
        subprocess.run([
            self.adb_path, "-s", self.device_id, "shell", "am", "start",
            "-n", f"{self.chrome_package}/com.google.android.apps.chrome.Main"
        ])
        time.sleep(3)
        print("Chrome started")
    
    def _navigate_to_shopee_login(self):
        """Navigate to Shopee login page"""
        # Use ADB to input URL (simplified - in practice, you'd use UI automation)
        login_url = "https://shopee.tw/buyer/login"
        subprocess.run([
            self.adb_path, "-s", self.device_id, "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", login_url
        ])
        time.sleep(5)
        print("Navigated to Shopee login")
    
    def _verify_login_status(self) -> bool:
        """Verify successful login"""
        # In practice, you would check for login indicators
        # This is a simplified placeholder
        return True
    
    def navigate_to_product(self, product_url: str):
        """Navigate to specific product page"""
        subprocess.run([
            self.adb_path, "-s", self.device_id, "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", product_url
        ])
        time.sleep(3)
        print(f"Navigated to: {product_url}")

class NetworkTrafficCapture:
    """Captures network traffic through ADB monitoring"""
    
    def __init__(self, adb_path: str = "adb"):
        self.adb_path = adb_path
        self.device_id = "emulator-5554"
        self.capture_queue = queue.Queue()
        self.is_capturing = False
        
    def start_traffic_capture(self):
        """Start capturing network traffic"""
        self.is_capturing = True
        
        # Start network capture in separate thread
        capture_thread = threading.Thread(target=self._capture_network_traffic)
        capture_thread.daemon = True
        capture_thread.start()
        
        print("Network traffic capture started")
    
    def _capture_network_traffic(self):
        """Capture HTTP/HTTPS traffic through ADB logcat"""
        try:
            # Monitor network requests via logcat
            cmd = [
                self.adb_path, "-s", self.device_id, "logcat", "-v", "time",
                "chromium:V", "*:S"
            ]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                if not self.is_capturing:
                    break
                    
                # Filter for Shopee API endpoints
                if self._is_shopee_api_request(line):
                    self.capture_queue.put({
                        'timestamp': datetime.now().isoformat(),
                        'log_line': line.strip()
                    })
                    
        except Exception as e:
            print(f"Error in network capture: {e}")
    
    def _is_shopee_api_request(self, log_line: str) -> bool:
        """Check if log line contains Shopee API request"""
        api_patterns = [
            r'shopee\.tw/api/v4/pdp/get_pc',
            r'shopee\.tw/api/v4/item/get',
            r'shopee\.tw/api/v4/product/get_shop_info'
        ]
        
        return any(re.search(pattern, log_line) for pattern in api_patterns)
    
    def get_captured_data(self) -> List[Dict]:
        """Retrieve captured network data"""
        captured_data = []
        
        while not self.capture_queue.empty():
            try:
                data = self.capture_queue.get_nowait()
                captured_data.append(data)
            except queue.Empty:
                break
                
        return captured_data
    
    def stop_traffic_capture(self):
        """Stop network traffic capture"""
        self.is_capturing = False
        print("Network traffic capture stopped")

class ShopeeDataProcessor:
    """Processes extracted Shopee product data"""
    
    def process_mobile_api_response(self, response_data: str) -> Dict:
        """Process product data from mobile API responses"""
        try:
            # Extract JSON from log line (simplified)
            json_match = re.search(r'\{.*\}', response_data)
            if not json_match:
                return {}
                
            json_str = json_match.group()
            data = json.loads(json_str)
            
            # Extract product information
            product_info = {
                'product_id': data.get('item', {}).get('itemid'),
                'shop_id': data.get('item', {}).get('shopid'),
                'name': data.get('item', {}).get('name'),
                'price': data.get('item', {}).get('price'),
                'stock': data.get('item', {}).get('stock'),
                'rating': data.get('item', {}).get('item_rating', {}).get('rating_star'),
                'sold_count': data.get('item', {}).get('sold'),
                'description': data.get('item', {}).get('description'),
                'images': [img.get('image') for img in data.get('item', {}).get('images', [])],
                'extracted_at': datetime.now().isoformat()
            }
            
            return product_info
            
        except Exception as e:
            print(f"Error processing API response: {e}")
            return {}

class MobileShopeeScraperTemplate:
    """Main template class for mobile Shopee scraping"""
    
    def __init__(self):
        self.emulator_manager = AndroidEmulatorManager()
        self.chrome_manager = MobileChromeManager()
        self.network_capture = NetworkTrafficCapture()
        self.data_processor = ShopeeDataProcessor()
        
    def setup_scraping_environment(self) -> bool:
        """Setup complete scraping environment"""
        print("Setting up mobile scraping environment...")
        
        # Step 1: Start Android emulator
        if not self.emulator_manager.start_emulator():
            return False
            
        # Step 2: Setup mobile Chrome session
        if not self.chrome_manager.setup_mobile_chrome_session():
            return False
            
        # Step 3: Start network traffic capture
        self.network_capture.start_traffic_capture()
        
        print("Mobile scraping environment ready!")
        return True
    
    def scrape_product_data(self, product_urls: List[str]) -> List[Dict]:
        """Scrape product data from list of URLs"""
        scraped_data = []
        
        for url in product_urls:
            try:
                print(f"Scraping: {url}")
                
                # Navigate to product page
                self.chrome_manager.navigate_to_product(url)
                
                # Wait for page load and API calls
                time.sleep(10)
                
                # Collect captured network data
                captured_data = self.network_capture.get_captured_data()
                
                # Process each captured API response
                for capture in captured_data:
                    product_data = self.data_processor.process_mobile_api_response(
                        capture['log_line']
                    )
                    if product_data:
                        product_data['source_url'] = url
                        scraped_data.append(product_data)
                        
                # Add delay between requests
                time.sleep(5)
                
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue
                
        return scraped_data
    
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up resources...")
        self.network_capture.stop_traffic_capture()
        self.emulator_manager.stop_emulator()
        print("Cleanup completed")

def main():
    """Main execution function"""
    
    # Initialize scraper
    scraper = MobileShopeeScraperTemplate()
    
    try:
        # Setup environment
        if not scraper.setup_scraping_environment():
            print("Failed to setup scraping environment")
            return
            
        # Define target URLs
        product_urls = [
            "https://shopee.tw/product/123456/789012",
            "https://shopee.tw/product/234567/890123",
            # Add more URLs as needed
        ]
        
        # Scrape product data
        print("Starting product data scraping...")
        scraped_data = scraper.scrape_product_data(product_urls)
        
        # Save results
        with open('shopee_mobile_scraped_data.json', 'w', encoding='utf-8') as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=2)
            
        print(f"Scraping completed! Extracted {len(scraped_data)} products")
        
    except KeyboardInterrupt:
        print("Scraping interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Always cleanup
        scraper.cleanup()

if __name__ == "__main__":
    main()
