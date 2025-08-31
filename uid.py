import requests

def get_id(link):
    url = "https://id.traodoisub.com/api.php"
    headers = {
        "authority": "id.traodoisub.com",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://id.traodoisub.com",
        "referer": "https://id.traodoisub.com/",
        "sec-ch-ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    data = {"link": link}
    try:
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except requests.RequestException:
        return None

def main():
    print("🔍 Tool lấy UID Facebook từ link")
    links = input("📋 Nhập link Facebook (cách nhau bằng dấu phẩy): ").strip().split(",")
    links = [link.strip() for link in links if link.strip()]  
    
    if not links:
        print("❌ Vui lòng nhập ít nhất một link.")
        return
    
    print("\n📊 Kết quả lấy UID:")
    for link in links:
        print(f"⏳ Đang xử lý link: {link}...")
        uid = get_id(link)
        if uid:
            print(f"✅ Link: {link} → UID: {uid}")
        else:
            print(f"❌ Link: {link} → Không lấy được UID")

if __name__ == "__main__":
    main()