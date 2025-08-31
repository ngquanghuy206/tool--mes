import requests
import os
import tempfile

def get_facebook_avatar(uid):
    api_url = f"https://keyherlyswar.x10.mx/Apidocs/avtfb.php?uid={uid}"
    response = requests.get(api_url)
    
    if response.status_code == 200 and response.headers.get('content-type').startswith('image'):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        return temp_file_path
    return None

def upload_image_catbox(filepath):
    url = "https://catbox.moe/user/api.php"
    with open(filepath, 'rb') as f:
        files = {
            'reqtype': (None, 'fileupload'),
            'fileToUpload': (os.path.basename(filepath), f)
        }
        response = requests.post(url, files=files)
        return response.text if response.status_code == 200 else None

def main():
    uid = input("📷 Nhập UID Facebook: ").strip()
    
    print(f"⏳ Đang lấy avatar cho UID: {uid}...")
    temp_image_path = get_facebook_avatar(uid)
    
    if not temp_image_path:
        print("❌ Không thể lấy được avatar từ API.")
        return
    

    print("⬆️ Đang upload avatar lên Catbox...")
    link = upload_image_catbox(temp_image_path)
    

    os.unlink(temp_image_path)
    
    if link and "catbox" in link:
        print(f"✅ Link avatar: {link}")
    else:
        print("❌ Lỗi khi upload ảnh lên Catbox.")

if __name__ == "__main__":
    main()