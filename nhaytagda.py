
import requests 
import os
import re
import json
import time
import random
import datetime
import threading
from typing import Dict, Any
import pyfiglet

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')
    
class Mention:
    thread_id = None
    offset = None
    length = None

    def __init__(self, thread_id, offset, length):
        self.thread_id = thread_id
        self.offset = offset
        self.length = length

    @classmethod
    def _from_range(cls, data):
        return cls(
            thread_id=data["entity"].get("id"),
            offset=data["offset"],
            length=data["length"],
        )

    @classmethod
    def _from_prng(cls, data):
        return cls(thread_id=data["i"], offset=data["o"], length=data["l"])

    def _to_send_data(self, i):
        return {
            "profile_xmd[{}][id]".format(i): self.thread_id,
            "profile_xmd[{}][offset]".format(i): self.offset,
            "profile_xmd[{}][length]".format(i): self.length,
            "profile_xmd[{}][type]".format(i): "p",
        }


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
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["id"]
    else:
        return None
        
def AnkLaDontCry(cookie_str):
    cookies = {}
    cookie_items = cookie_str.split(';')
    for item in cookie_items:
        parts = item.strip().split('=', 1)
        if len(parts) == 2:
            cookies[parts[0].strip()] = parts[1].strip()
    return cookies

def get_du_lieu(ck):
    try:
        response = requests.get("https://m.facebook.com/", cookies=AnkLaDontCry(ck))
        response.raise_for_status()
        if 'fb_dtsg' in response.text:
            fb_dtsg = response.text.split('<input type="hidden" name="fb_dtsg" value="')[1].split('"')[0]
            return fb_dtsg
        else:
            return None
    except Exception as e:
        print(f"Lỗi khi gửi yêu cầu: {e}")
        return None
        
def check_live(cookie):
    try:
        if 'c_user=' not in cookie:
            return {"status": "failed", "msg": "Cookie không chứa user_id"}
        
        user_id = cookie.split('c_user=')[1].split(';')[0]

        url = f"https://graph2.facebook.com/v3.3/{user_id}/picture?redirect=0"
        response = requests.get(url, timeout=30)
        check_data = response.json()

        if not check_data.get('data', {}).get('height') or not check_data.get('data', {}).get('width'):
            return {"status": "failed", "msg": "Cookie không hợp lệ"}

        headers = {
            'authority': 'm.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'vi-VN,vi;q=0.9',
            'cache-control': 'max-age=0',
            'cookie': cookie,
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"0.1.0"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }

        profile_response = requests.get(f'https://m.facebook.com/profile.php?id={user_id}', headers=headers, timeout=30)
        name = profile_response.text.split('<title>')[1].split('<')[0].strip()

        return {
            "status": "success",
            "name": name,
            "user_id": user_id,
            "msg": "successful"
        }

    except Exception as e:
        return {"status": "failed", "msg": f"Lỗi xảy ra: {str(e)}"}

def get_name(id, cookie):
    headers = {
        'authority': 'm.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5,zh-CN;q=0.4,zh;q=0.3,gom;q=0.2,und;q=0.1',
        'cache-control': 'max-age=0',
        'cookie': cookie,
        'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"0.1.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
    }
    try:
        name = requests.get(f'https://m.facebook.com/profile.php?id={id}', headers=headers).text.split('<title>')[1].split('<')[0]
        return name
    except:
        return None

def fake_typing(cookie, thread_id, user_id):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Accept-Language": "vi-VN,vi;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.facebook.com",
        "Referer": f"https://www.facebook.com/messages/t/{thread_id}",
        "Cookie": cookie
    }

    fb_dtsg = get_du_lieu(cookie)
    if not fb_dtsg:
        print("Không lấy được fb_dtsg.")
        return False

    payload = {
        "typ": "1",
        "to": thread_id,
        "source": "source:chat:web",
        "thread": thread_id,
        "fb_dtsg": fb_dtsg,
        "__user": user_id,
        "__a": "1",
        "__req": "1b",
        "__rev": "1006632069"
    }

    try:
        res = requests.post("https://www.facebook.com/ajax/messaging/typ.php", headers=headers, data=payload)
        if res.status_code == 200 and "for (;;);" in res.text:
            return True
        else:
            print("Lỗi fake typing:", res.text)
            return False
    except Exception as e:
        print(f"Lỗi gửi fake typing: {e}")
        return False


def send_message(cookie, idbox, content, list_tag, user_id, list_name_tag):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Cookie': cookie,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://www.facebook.com',
        'Referer': f'https://www.facebook.com/messages/t/{idbox}'
    }
    
    tag_parts = []
    mentions = []
    offset = len(content) + 1
    for i in range(len(list_tag)):
        name = list_name_tag[i]
        tag_text = f"@{name}"
        tag_parts.append(tag_text)

        mention = Mention(thread_id=list_tag[i], offset=offset, length=len(tag_text))
        mentions.append(mention)
        offset += len(tag_text) + 1

    full_message = f"{content} {' '.join(tag_parts)}"
    ts = str(int(time.time() * 1000))
    fb_dtsg = get_du_lieu(cookie)
    
    if fb_dtsg:
        payload = {
            "thread_fbid": idbox,
            "action_type": "ma-type:user-generated-message",
            "body": full_message,
            "client": "mercury",
            "author": f"fbid:{user_id}",
            "timestamp": ts,
            "offline_threading_id": ts,
            "message_id": ts,
            "source": "source:chat:web",
            "ephemeral_ttl_mode": "0",
            "__user": user_id,
            "__a": '1',
            "__req": '1b',
            "__rev": '1015919737',
            "fb_dtsg": fb_dtsg,
            "source_tags[0]": "source:chat"
        }
 
        for idx, mention in enumerate(mentions):
            payload.update(mention._to_send_data(idx))

        try:
            response = requests.post("https://www.facebook.com/messaging/send/", headers=headers, data=payload, timeout=10)
            return "success" if response.status_code == 200 else "failed"
        except:
            return "failed"
    else:
        return "failed"

def main():
    clear()
    print(pyfiglet.figlet_format('NgQuangHuy', font="slant"))
    ck_list = []
    ten_ck = []
    id_acc = []
    stt_ck = 0
    while True:
        stt_ck += 1
        ck_nhap = input(f"Nhập cookie lần {stt_ck} hoặc nhập 'xong' để dừng : ")
        if ck_nhap.lower() == 'xong':
            break
        cl = check_live(ck_nhap)
        if cl["status"] == "success":
            print(f'Cookie Live ! Name : {cl["name"]}')
            ck_list.append(ck_nhap)
            ten_ck.append(cl["name"])
            id_acc.append(cl["user_id"])
        else:
            stt_ck -= 1
            print('Cookie sai !')

    id_list = []
    stt = 0
    while True:
        stt += 1
        idcanspam = input(f"Nhập id box cần spam thứ {stt} hoặc nhập 'xong': ")
        if idcanspam.lower() == 'xong':
            break
        if idcanspam != '':
            id_list.append(idcanspam)

    while True:
        file_ngon = input('Nhập tên file chứa ngôn : ')
        if os.path.exists(file_ngon):
            break
        else:
            print(f"Không tìm thấy file '{file_ngon}'! Vui lòng thử lại")

    with open(file_ngon, "r", encoding="utf-8") as file:
        nd_list = [f"{line.strip()}" for line in file.readlines()]

    tp = input("Nhập nội dung bạn muốn thay thế cho {name} : ")
    list_tag = []
    name_th_ngu = []
    stt_tag = 0
    while True:
        stt_tag += 1
        link = input(f"Nhập link facebook cần nhây tag lần {stt_tag} hoặc nhập 'xong' : ")
        if link.lower() == "xong":
            break
        id = get_id(link)
        if id:
            list_tag.append(id)
            name = get_name(id, ck_list[0])
            if name:
                name_th_ngu.append(name)
                print(f'Đã thêm {name} vào danh sách tag')
            else:
                print('Lỗi khi lấy name')
                return
        else:
            print('Lỗi khi lấy id')

    delay = int(input('Nhập delay : '))
    m = 0
    stts = 0
    clear()
    while True:
        for id_box in id_list:
            for ngon in nd_list:
                message = ngon.replace("{name}", tp)
                status = send_message(ck_list[m], id_box, message, list_tag, id_acc[m], name_th_ngu)
                if status == "success":
                    stts += 1
                    print(f" - [ Account : {ten_ck[m]} ] Gửi nội dung {message} đến {id_box} lần {stts} thành công.")
                else:
                    print(f" - [ Account : {ten_ck[m]} ] Gửi Thất Bại")

                m = (m + 1) % len(ck_list)
                
                time.sleep(delay)                    
main()