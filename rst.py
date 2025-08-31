import requests
import os
import json
import re
import time
from html import unescape
from io import BytesIO

def get_uid_fbdtsg(ck):
    try:
        headers = {
            'Accept': 'text/html',
            'Cookie': ck,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        }

        response = requests.get('https://www.facebook.com/', headers=headers)
        html_content = response.text

        if "home_icon" not in html_content and '"USER_ID":"' not in html_content:
            return None, None, None, None, None, None

        user_id = re.search(r'"USER_ID":"(\d+)"', html_content)
        user_id = user_id.group(1) if user_id else None

        fb_dtsg_match = re.search(r'"f":"([^"]+)"', html_content)
        fb_dtsg = fb_dtsg_match.group(1) if fb_dtsg_match else None

        jazoest_match = re.search(r'jazoest=(\d+)', html_content)
        jazoest = jazoest_match.group(1) if jazoest_match else None

        revision_match = re.search(r'"server_revision":(\d+),"client_revision":(\d+)', html_content)
        rev = revision_match.group(1) if revision_match else ""

        a_match = re.search(r'__a=(\d+)', html_content)
        a = a_match.group(1) if a_match else "1"

        req = "1b"

        if not user_id or not fb_dtsg:
            return None, None, None, None, None, None

        return user_id, fb_dtsg, rev, req, a, jazoest

    except Exception as e:
        print(f"Lỗi Khi Check Cookie: {e}")
        return None, None, None, None, None, None


def upload_image_get_fbid(image_path_or_url: str, ck: str) -> str:
    user_id, fb_dtsg, rev, req, a, jazoest = get_uid_fbdtsg(ck)
    if not all([user_id, fb_dtsg, jazoest]):
        return "Không thể lấy thông tin từ cookie. Vui lòng kiểm tra lại."

    is_url = image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://")
    try:
        if is_url:
            resp = requests.get(image_path_or_url)
            if resp.status_code != 200:
                return "Không thể tải ảnh từ URL."
            img_data = BytesIO(resp.content)
            img_data.name = "image.jpg"
        else:
            if not os.path.isfile(image_path_or_url):
                return "File không tồn tại. Hãy nhập đúng đường dẫn tới ảnh."
            img_data = open(image_path_or_url, 'rb')
    except Exception as e:
        return f"Lỗi khi đọc ảnh: {e}"

    headers = {
        'cookie': ck,
        'origin': 'https://www.facebook.com',
        'referer': 'https://www.facebook.com/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64)',
        'x-fb-lsd': fb_dtsg,
    }

    params = {
        'av': user_id,
        'profile_id': user_id,
        'source': '19',
        'target_id': user_id,
        '__user': user_id,
        '__a': a,
        '__req': req,
        '__rev': rev,
        'fb_dtsg': fb_dtsg,
        'jazoest': jazoest,
    }

    try:
        files = {
            'file': (img_data.name, img_data, 'image/jpeg')
        }

        response = requests.post(
            'https://www.facebook.com/ajax/ufi/upload/',
            headers=headers,
            params=params,
            files=files
        )

        if is_url:
            img_data.close()

        text = response.text.strip()
        if text.startswith("for(;;);"):
            text = text[8:]

        try:
            data = json.loads(text)
            fbid = data.get("payload", {}).get("fbid")
            if fbid:
                return fbid
            return "Không tìm thấy fbid trong JSON."

        except json.JSONDecodeError:
            match = re.search(r'"fbid"\s*:\s*"(\d+)"', text)
            if match:
                return match.group(1)
            return "Không tìm thấy fbid trong text."

    except Exception as e:
        return f"Lỗi khi upload: {e}"



ck = input("Nhập cookie Facebook: ")
image_input = input("Nhập đường dẫn hoặc URL ảnh: ")
mention = input("Nhập ID người cần tag: ")
delay_seconds = float(input("Nhập thời gian delay giữa mỗi lần gửi (giây): "))

user_id, fb_dtsg, rev, req, a, jazoest = get_uid_fbdtsg(ck)

headers = {
    'content-type': 'application/x-www-form-urlencoded',
    'cookie': ck,
    'origin': 'https://www.facebook.com',
    'referer': 'https://www.facebook.com/stories/create',
    'user-agent': 'Mozilla/5.0',
    'x-fb-friendly-name': 'StoriesCreateMutation',
    'x-fb-lsd': fb_dtsg,
}


if not os.path.exists("nhay.txt"):
    print("Không tìm thấy file nhay.txt")
    exit()

with open("nhay.txt", "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

for content_text in lines:
    fbid = upload_image_get_fbid(image_input, ck)

    variables = {
        "input": {
            "audiences": [{"stories": {"self": {"target_id": user_id}}}],
            "audiences_is_complete": True,
            "logging": {"composer_session_id": ""},
            "navigation_data": {
                "attribution_id_v2": "StoriesCreateRoot.react,comet.stories.create,..."
            },
            "source": "WWW",
            "message": {"ranges": [], "text": content_text},
            "attachments": [{
                "photo": {
                    "id": fbid,
                    "overlays": [
                        {
                            "tag_sticker": {
                                "bounds": {
                                    "height": 0.0356,
                                    "rotation": 0,
                                    "width": 0.3764,
                                    "x": 0.3944,
                                    "y": 0.4582
                                },
                                "creation_source": "TEXT_TOOL_MENTION",
                                "tag_id": mention,
                                "type": "PEOPLE"
                            }
                        }
                    ]
                }
            }],
            "tracking": [None],
            "actor_id": user_id,
            "client_mutation_id": str(time.time())
        }
    }

    data = {
        '__user': user_id,
        '__a': a,
        '__req': req,
        'fb_dtsg': fb_dtsg,
        'jazoest': jazoest,
        'lsd': fb_dtsg,
        'variables': json.dumps(variables),
        'doc_id': '7490607150987409',
    }

    try:
        response = requests.post('https://www.facebook.com/api/graphql/', headers=headers, data=data)
        print("✅ Gửi story thành công:", response.json())
    except Exception as e:
        print("❌ Lỗi khi gửi:", e)
        print("Response text:", response.text)

    time.sleep(delay_seconds)