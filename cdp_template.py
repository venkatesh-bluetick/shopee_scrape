import pychrome
import subprocess
import tempfile
import time
import base64

def launch_chrome_with_debugging():
    """Launch Chrome with remote debugging enabled"""
    chrome_path = "/path/to/chrome"  # Adjust for your system
    temp_profile = tempfile.mkdtemp(prefix="chrome_profile_")
    
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={temp_profile}",
        "--no-first-run",
        # Additional flags for stealth operation
    ]
    return subprocess.Popen(cmd)

def main():
    # Step 1: Launch Chrome process
    chrome_process = launch_chrome_with_debugging()
    time.sleep(3)  # Allow Chrome to initialize
    
    # Step 2: Connect to Chrome via CDP
    browser = pychrome.Browser(url="http://127.0.0.1:9222")
    tab = browser.new_tab()
    
    # Step 3: Configure network event callbacks
    requests_tracker = {}
    
    def on_request_will_be_sent(**kwargs):
        request_id = kwargs.get("requestId")
        request_url = kwargs.get("request", {}).get("url")
        requests_tracker[request_id] = {"url": request_url}
    
    def on_response_received(**kwargs):
        request_id = kwargs.get("requestId")
        response = kwargs.get("response", {})
        if request_id in requests_tracker:
            requests_tracker[request_id]["status"] = response.get("status")
    
    def on_loading_finished(**kwargs):
        request_id = kwargs.get("requestId")
        url = requests_tracker.get(request_id, {}).get("url", "")
        
        # Filter for Shopee product API endpoints
        if "shopee.tw/api/v4/pdp/get_pc" in url:
            try:
                # Extract response body via CDP
                result = tab.Network.getResponseBody(requestId=request_id)
                body = result.get("body", "")
                
                if result.get("base64Encoded", False):
                    body = base64.b64decode(body).decode("utf-8")
                
                # Process the product data
                process_product_data(body, url)
                
            except Exception as e:
                print(f"Error extracting response: {e}")
    
    # Step 4: Attach event handlers and enable network monitoring
    tab.Network.requestWillBeSent = on_request_will_be_sent
    tab.Network.responseReceived = on_response_received
    tab.Network.loadingFinished = on_loading_finished
    
    # Start tab and enable network domain
    tab.start()
    tab.Network.enable()
    
    # Step 5: Navigate to Shopee product pages
    product_urls = [
        "https://shopee.tw/product/12345/67890",
        # Add more URLs as needed
    ]
    
    for url in product_urls:
        print(f"Navigating to: {url}")
        tab.Page.navigate(url=url)
        time.sleep(15)  # Allow page to load and API calls to complete
        
        # Optional: Clear session data between requests
        tab.Network.clearBrowserCookies()
        tab.Network.clearBrowserCache()
    
    # Cleanup
    tab.stop()
    browser.close_tab(tab)
    chrome_process.terminate()

def process_product_data(response_body, api_url):
    """Process extracted product data from API response"""
    # Parse JSON response and extract product details
    # Implement your data processing logic here
    pass

if __name__ == "__main__":
    main()
