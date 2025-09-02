import requests
import json
import re
import time
import random

class FacebookThreadExtractor:
    def __init__(self, cookie):
        self.cookie = cookie
        self.session = requests.Session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        ]
        self.facebook_tokens = {}
        
    def get_facebook_tokens(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }
        
        sites = ['https://www.facebook.com', 'https://mbasic.facebook.com']
        
        for site in sites:
            try:
                response = self.session.get(site, headers=headers, timeout=10)
                c_user_match = re.search(r"c_user=(\d+)", self.cookie)
                if c_user_match:
                    self.facebook_tokens["FacebookID"] = c_user_match.group(1)
                
                fb_dtsg_match = re.search(r'"token":"(.*?)"', response.text) or re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
                if fb_dtsg_match:
                    self.facebook_tokens["fb_dtsg"] = fb_dtsg_match.group(1)
                
                jazoest_match = re.search(r'jazoest=(\d+)', response.text)
                if jazoest_match:
                    self.facebook_tokens["jazoest"] = jazoest_match.group(1)
                
                if self.facebook_tokens.get("fb_dtsg") and self.facebook_tokens.get("jazoest"):
                    break
                    
            except Exception:
                continue
        
        self.facebook_tokens.update({
            "__rev": "1015919737",
            "__req": "1b",
            "__a": "1",
            "__comet_req": "15"
        })
        
        return len(self.facebook_tokens) > 4
    
    def get_thread_list(self, limit=100):
        if not self.get_facebook_tokens():
            return {"error": "Không thể lấy token từ Facebook. Kiểm tra lại cookie."}
        
        form_data = {
            "av": self.facebook_tokens.get("FacebookID", ""),
            "__user": self.facebook_tokens.get("FacebookID", ""),
            "__a": self.facebook_tokens["__a"],
            "__req": self.facebook_tokens["__req"],
            "__hs": "19234.HYP:comet_pkg.2.1..2.1",
            "dpr": "1",
            "__ccg": "EXCELLENT",
            "__rev": self.facebook_tokens["__rev"],
            "__comet_req": self.facebook_tokens["__comet_req"],
            "fb_dtsg": self.facebook_tokens.get("fb_dtsg", ""),
            "jazoest": self.facebook_tokens.get("jazoest", ""),
            "lsd": "null",
            "__spin_r": self.facebook_tokens.get("client_revision", ""),
            "__spin_b": "trunk",
            "__spin_t": str(int(time.time())),
        }
        
        queries = {
            "o0": {
                "doc_id": "3336396659757871",
                "query_params": {
                    "limit": limit,
                    "before": None,
                    "tags": ["INBOX"],
                    "includeDeliveryReceipts": False,
                    "includeSeqID": True,
                }
            }
        }
        
        form_data["queries"] = json.dumps(queries)
        
        headers = {
            'Cookie': self.cookie,
            'User-Agent': random.choice(self.user_agents),
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Origin': 'https://www.facebook.com',
            'Referer': 'https://www.facebook.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-FB-Friendly-Name': 'MessengerThreadListQuery',
            'X-FB-LSD': 'null'
        }
        
        try:
            response = self.session.post(
                'https://www.facebook.com/api/graphqlbatch/',
                data=form_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code != 200:
                return {"error": f"HTTP Error: {response.status_code}"}
            
            response_text = response.text.split('{"successful_results"')[0]
            data = json.loads(response_text)
            
            if "o0" not in data:
                return {"error": "Không tìm thấy dữ liệu thread list"}
            
            if "errors" in data["o0"]:
                return {"error": f"Facebook API Error: {data['o0']['errors'][0]['summary']}"}
            
            threads = data["o0"]["data"]["viewer"]["message_threads"]["nodes"]
            thread_list = []
            
            for thread in threads:
                if not thread.get("thread_key") or not thread["thread_key"].get("thread_fbid"):
                    continue
                
                thread_list.append({
                    "thread_id": thread["thread_key"]["thread_fbid"],
                    "thread_name": thread.get("name", "Không có tên")
                })
            
            return {
                "success": True,
                "thread_count": len(thread_list),
                "threads": thread_list
            }
            
        except json.JSONDecodeError as e:
            return {"error": f"Lỗi parse JSON: {str(e)}"}
        except Exception as e:
            return {"error": f"Lỗi không xác định: {str(e)}"}

def save_to_file(threads, filename="box_list.txt"):
    """Lưu danh sách box vào file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("       DANH SÁCH BOX FACEBOOK\n")
            f.write("=" * 50 + "\n\n")
            
            for i, thread in enumerate(threads, 1):
                thread_name = thread.get('thread_name', 'Không có tên') or 'Không có tên'
                f.write(f"{i}. Tên: {thread_name}\n")
                f.write(f"   ID: {thread['thread_id']}\n")
                f.write("-" * 40 + "\n")
        
        print(f"✅ Đã lưu danh sách vào file: {filename}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi lưu file: {e}")
        return False

def main():
    print("═══════════════════════════════════════")
    print("      📋 TOOL LẤY DANH SÁCH BOX FB")
    print("═══════════════════════════════════════")
    
    cookie = input("Nhập Cookie Facebook: ").strip()
    
    try:
        limit = int(input("Nhập số lượng box cần lấy (mặc định 100): ").strip() or "100")
        if limit < 1 or limit > 500:
            limit = 100
            print("Số lượng không hợp lệ, sử dụng mặc định 100")
    except ValueError:
        limit = 100
        print("Số lượng không hợp lệ, sử dụng mặc định 100")
    
    print(f"\n🔍 Đang lấy danh sách {limit} box...")
    
    # Lấy dữ liệu box
    extractor = FacebookThreadExtractor(cookie)
    result = extractor.get_thread_list(limit=limit)
    
    if "error" in result:
        print(f"❌ Lỗi: {result['error']}")
        return
    
    threads = result['threads']
    
    if not threads:
        print("❌ Không tìm thấy box nào!")
        return
    
    print(f"\n✅ Tìm thấy {len(threads)} box:")
    print("=" * 60)
    
    # Hiển thị danh sách
    for i, thread in enumerate(threads, 1):
        thread_name = thread.get('thread_name', 'Không có tên') or 'Không có tên'
        display_name = f"{thread_name[:45]}{'...' if len(thread_name) > 45 else ''}"
        
        print(f"{i:3d}. {display_name}")
        print(f"     ID: {thread['thread_id']}")
        print("-" * 55)
    
    # Hỏi có muốn lưu file không
    save_choice = input("\n💾 Bạn có muốn lưu danh sách vào file? (y/n): ").strip().lower()
    
    if save_choice in ['y', 'yes', 'có']:
        filename = input("Nhập tên file (để trống sẽ dùng 'box_list.txt'): ").strip()
        if not filename:
            filename = "box_list.txt"
        if not filename.endswith('.txt'):
            filename += '.txt'
        
        save_to_file(threads, filename)
    
    print(f"\n✨ Hoàn thành! Đã lấy {len(threads)} box")

if __name__ == "__main__":
    main()