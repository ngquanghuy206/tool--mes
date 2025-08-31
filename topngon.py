import requests
import re
import time
import os

os.system('cls' if os.name == 'nt' else 'clear')

def visual_delay(t):
    print(f"Chờ {int(t)} giây để qua bình luận tiếp theo...", end='\r')
    time.sleep(t)
    print(" " * 50, end='\r')  # Xóa dòng chờ

def check_login_facebook(cookie):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Cookie": cookie
        }
        response = requests.get("https://m.facebook.com/", headers=headers).text
        name_match = re.search(r'<title>(.*?)</title>', response)

        if name_match:
            name = name_match.group(1).replace(" | Facebook", "").strip()
            return name, None, None, "Unknown"
        else:
            print("Không tìm thấy thông tin tên người dùng.")
            return False
    except Exception as e:
        print(f"Lỗi khi kiểm tra đăng nhập: {e}")
        return False

def get_token(cookie):
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5',
        'cache-control': 'max-age=0',
        'cookie': cookie,
        'dpr': '1',
        'priority': 'u=0, i',
        'sec-ch-prefers-color-scheme': 'light',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="125.0.6422.78", "Chromium";v="125.0.6422.78", "Not.A/Brand";v="24.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"10.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'viewport-width': '868',
    }

    try:
        response = requests.get('https://business.facebook.com/content_management', headers=headers).text
        token = response.split('[{"accessToken":"')[1].split('","')[0]
        return token
    except Exception as e:
        print("Lấy token thất bại!")
        return None

def auto_cmt_moi_ne(access_token, idpost, mess, cookie):
    data = {
        "access_token": access_token,
        "message": mess
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-A750GN) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.106 Mobile Safari/537.36",
        "Cookie": cookie
    }

    response = requests.post(f"https://graph.facebook.com/{idpost}/comments", data=data, headers=headers)
    res = response.text

    if "An unknown error occurred" in res or '"fbtrace_id":' in res:
        return "1"

    result = response.json()

    if "error" in result:
        return {"status": "die", "msg": result["error"]["message"]}
    else:
        return result

def load_cookies(file_path):
    try:
        with open(file_path, 'r') as file:
            cookies = file.readlines()
            cookies = [cookie.strip() for cookie in cookies if cookie.strip()]
        return cookies
    except Exception as e:
        print(f"Lỗi khi đọc file cookie: {e}")
        return []

def get_all_content_and_count_from_file(file_path, empty_file_message):
    if not os.path.exists(file_path):
        return "Tệp không tồn tại.", 0
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        return empty_file_message, 0
    combined_content = "\n".join(lines)
    return combined_content, len(lines)

file_path_comment = "comment.txt"

def main():
    comment_text, comment_count = get_all_content_and_count_from_file(file_path_comment, "Không có bình luận nào trong tệp.")
    cookies = load_cookies("cookie.txt")
    if not cookies:
        print("Không tải được cookie.")
        return
    print(f"Số lượng cookie đã tải: {len(cookies)}")
    print(f"Số lượng dòng comment đã tải: {comment_count}")
    idpost = int(input("ID Post: "))
    dem = int(input("Nhập số lần comment: "))
    delay_min = float(input("Nhập thời gian chờ tối thiểu (giây): "))
    delay_max = float(input("Nhập thời gian chờ tốiA đa (giây): "))
    tagbb = input("Comment tag (Y/N): ").strip().upper()
    chongspam = input("Kích hoạt chống spam (Y/N): ").strip().upper()
    switch_after = int(input("Đổi cookie sau bao nhiêu lần comment: "))
    idbb = int(input("Nhập ID cần tag: ")) if tagbb == "Y" else None
    print("\n================= Bắt đầu chạy =================\n")
    current_cookie_index = 0
    cookie_logged_in = False
    for i in range(dem):
        if i % switch_after == 0 and i != 0:
            current_cookie_index = (current_cookie_index + 1) % len(cookies)
            cookie_logged_in = False
            time.sleep(2)

        cookie = cookies[current_cookie_index]
        try:
            if not cookie_logged_in:
                login_info = check_login_facebook(cookie)
                if login_info:
                    name, fb_dtsg, jazoest, idacc = login_info
                    print("--------------------------------------------------")
                    print(f"FaceBook: {name} | Uid: {idacc}")
                    print("--------------------------------------------------")
                    cookie_logged_in = True
                else:
                    print(f"Login thất bại với cookie {current_cookie_index + 1}. Chuyển sang cookie tiếp theo.")
                    continue

            if comment_text:
                noidung = comment_text
                if idbb:
                    noidung += f' @[{idbb}:0]'
                access_token = get_token(cookie)
                if access_token:
                    response = auto_cmt_moi_ne(access_token, idpost, noidung, cookie)
                    if response == "1":
                        print("Đã xảy ra lỗi khi đăng bình luận.")
                    else:
                        print(f"[{i+1}] Comment | {response.get('id')} | Đã gửi toàn bộ nội dung comment.txt | Thành công")
                        delay = random.uniform(delay_min, delay_max)
                        visual_delay(delay)
                        if i + 1 == dem:
                            print("Đã đạt được số lần comment đã nhập. Dừng lại.")
                            break
                else:
                    print("Lấy token thất bại")
            else:
                print("Không thể phân tích bình luận.")
        except Exception as e:
            print(f"Lỗi xảy ra: {e}")
            break

main()