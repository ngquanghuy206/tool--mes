import requests
import re
import json
import time
import random
from typing import Dict, Any


class FacebookPoster:
    def __init__(self, cookie):
        self.cookie = cookie
        self.fb_dtsg = None
        self.jazoest = None
        self.uid = None
        self.uppost_count = 0
        
        try:
            self.uid = self.id_user()
            self.init_params()
        except Exception as e:
            print(f"Lỗi khởi tạo: {str(e)}")
            exit()
    
    def id_user(self):
        try:
            c_user = re.search(r"c_user=(\d+)", self.cookie).group(1)
            return c_user
        except:
            raise Exception("Cookie không hợp lệ")

    def init_params(self):
        headers = {
            'Cookie': self.cookie,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate', 
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            response = requests.get('https://www.facebook.com', headers=headers)
            fb_dtsg_match = re.search(r'"token":"(.*?)"', response.text)
            
            jazoest_match = re.search(r'jazoest=(\d+)', response.text)
            if jazoest_match:
                self.jazoest = jazoest_match.group(1)
            
            if not fb_dtsg_match:
                response = requests.get('https://mbasic.facebook.com', headers=headers)
                fb_dtsg_match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
                
                if not fb_dtsg_match:
                    response = requests.get('https://m.facebook.com', headers=headers)
                    fb_dtsg_match = re.search(r'name="fb_dtsg" value="(.*?)"', response.text)
                
                if not jazoest_match:
                    jazoest_match = re.search(r'jazoest=(\d+)', response.text)
                    if jazoest_match:
                        self.jazoest = jazoest_match.group(1)

            if fb_dtsg_match:
                self.fb_dtsg = fb_dtsg_match.group(1)
            else:
                with open('debug_response.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                raise Exception("Không lấy được fb_dtsg")
            
            if not self.jazoest:
                raise Exception("Không lấy được jazoest")

        except Exception as e:
            raise Exception(f"Lỗi khi khởi tạo tham số: {str(e)}")

    def get_guid(self):
        section_length = int(time.time() * 1000)
        
        def replace_func(c):
            nonlocal section_length
            r = (section_length + random.randint(0, 15)) % 16
            section_length //= 16
            return hex(r if c == "x" else (r & 7) | 8)[2:]

        return "".join(replace_func(c) if c in "xy" else c for c in "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx")

    def get_info(self, uid):
        try:
            form = {
                "ids[0]": uid,
                "fb_dtsg": self.fb_dtsg,
                "__a": 1,
                "__req": "1b",
                "__rev": "1015919737"
            }
            
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
                'Connection': 'keep-alive',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Cookie': self.cookie,
                'Origin': 'https://www.facebook.com',
                'Referer': 'https://www.facebook.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (like Gecko) Chrome/122.0.0.0 Safari/537.36'
            }
            
            response = requests.post(
                "https://www.facebook.com/chat/user_info/",
                headers=headers,
                data=form
            )
            
            if response.status_code != 200:
                return {"error": f"Lỗi Kết Nối: {response.status_code}"}
            
            try:
                text_response = response.text
                if text_response.startswith("for (;;);"):
                    text_response = text_response[9:]
                
                res_data = json.loads(text_response)
                
                if "error" in res_data:
                    return {"error": res_data.get("error")}
                
                if "payload" in res_data and "profiles" in res_data["payload"]:
                    return self.format_data(res_data["payload"]["profiles"])
                else:
                    return {"error": f"Không Tìm Thấy Thông Tin Của {uid}"}
                    
            except json.JSONDecodeError:
                return {"error": "Lỗi Khi Phân Tích JSON"}
                
        except Exception as e:
            print(f"Lỗi Khi Get Info: {e}")
            return {"error": str(e)}

    def format_data(self, profiles):
        if not profiles:
            return {"error": "Không Có Data"}
        
        first_profile_id = next(iter(profiles))
        profile = profiles[first_profile_id]
        
        return {
            "id": first_profile_id,
            "name": profile.get("name", ""),
            "url": profile.get("url", ""),
            "thumbSrc": profile.get("thumbSrc", ""),
            "gender": profile.get("gender", "")
        }

    def create_post(self, message, tag_id, tag_name):
        try:
            idempotence_token = f"{self.get_guid()}_FEED"
            client_mutation_id = str(round(random.random() * 19))
            crt_time = int(time.time() * 1000)
            
            tag_format = random.choice([f"{tag_name} {message}", f"{message} {tag_name}"])
            
            if tag_format.startswith(tag_name):
                offset = 0
                length = len(tag_name)
            else:
                offset = len(message) + 1
                length = len(tag_name)
            
            variables = {
                "input": {
                    "composer_entry_point": "inline_composer",
                    "composer_source_surface": "newsfeed",
                    "composer_type": "feed",
                    "idempotence_token": idempotence_token,
                    "source": "WWW",
                    "audience": {
                        "privacy": {
                            "allow": [],
                            "base_state": "FRIENDS",
                            "deny": [],
                            "tag_expansion_state": "UNSPECIFIED"
                        }
                    },
                    "message": {
                        "ranges": [
                            {
                                "entity": {
                                    "id": tag_id
                                },
                                "length": length,
                                "offset": offset
                            }
                        ],
                        "text": tag_format
                    },
                    "inline_activities": [],
                    "text_format_preset_id": "0",
                    "publishing_flow": {
                        "supported_flows": ["ASYNC_SILENT", "ASYNC_NOTIF", "FALLBACK"]
                    },
                    "logging": {
                        "composer_session_id": idempotence_token.split("_")[0]
                    },
                    "navigation_data": {
                        "attribution_id_v2": f"CometHomeRoot.react,comet.home,via_cold_start,{crt_time},149902,4748854339,,"
                    },
                    "tracking": [],
                    "event_share_metadata": {
                        "surface": "newsfeed"
                    },
                    "actor_id": self.uid,
                    "client_mutation_id": client_mutation_id
                },
                "feedLocation": "NEWSFEED",
                "feedbackSource": 1,
                "focusCommentID": None,
                "gridMediaWidth": None,
                "groupID": None,
                "scale": 3,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "checkPhotosToReelsUpsellEligibility": True,
                "renderLocation": "homepage_stream",
                "useDefaultActor": False,
                "inviteShortLinkKey": None,
                "isFeed": True,
                "isFundraiser": False,
                "isFunFactPost": False,
                "isGroup": False,
                "isEvent": False,
                "isTimeline": False,
                "isSocialLearning": False,
                "isPageNewsFeed": False,
                "isProfileReviews": False,
                "isWorkSharedDraft": False,
                "hashtag": None,
                "canUserManageOffers": False,
                "__relay_internal__pv__CometUFIShareActionMigrationrelayprovider": True,
                "__relay_internal__pv__GHLShouldChangeSponsoredDataFieldNamerelayprovider": False,
                "__relay_internal__pv__GHLShouldChangeAdIdFieldNamerelayprovider": True,
                "__relay_internal__pv__CometIsReplyPagerDisabledrelayprovider": False,
                "__relay_internal__pv__IsWorkUserrelayprovider": False,
                "__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider": False,
                "__relay_internal__pv__FBReels_deprecate_short_form_video_context_gkrelayprovider": True,
                "__relay_internal__pv__CometFeedStoryDynamicResolutionPhotoAttachmentRenderer_experimentWidthrelayprovider": 500,
                "__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider": False,
                "__relay_internal__pv__WorkCometIsEmployeeGKProviderrelayprovider": False,
                "__relay_internal__pv__IsMergQAPollsrelayprovider": False,
                "__relay_internal__pv__FBReelsMediaFooter_comet_enable_reels_ads_gkrelayprovider": False,
                "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": False,
                "__relay_internal__pv__CometFeedPYMKHScrollInitialPaginationCountrelayprovider": 10,
                "__relay_internal__pv__FBReelsIFUTileContent_reelsIFUPlayOnHoverrelayprovider": False,
                "__relay_internal__pv__GHLShouldChangeSponsoredAuctionDistanceFieldNamerelayprovider": False
            }
            
            data = {
                "av": self.uid,
                "fb_dtsg": self.fb_dtsg,
                "jazoest": self.jazoest,
                "__crn": "comet.fbweb.CometHomeRoute",
                "fb_api_caller_class": "RelayModern",
                "fb_api_friendly_name": "ComposerStoryCreateMutation",
                "variables": json.dumps(variables),
                "server_timestamps": "true",
                "doc_id": "9676012065790356"
            }
            
            headers = {
                "Accept": "*/*",
                "Accept-Encoding": "identity",
                "Connection": "keep-alive",
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": self.cookie,
                "Origin": "https://www.facebook.com",
                "Referer": "https://www.facebook.com/",
                "User-Agent": "python-http/0.27.0"
            }
            
            response = requests.post(
                "https://www.facebook.com/api/graphql/",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                self.uppost_count += 1
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Lỗi khi đăng bài: {str(e)}")
            return False

    def run(self, tag_id):
        user_info = self.get_info(tag_id)
        if "error" in user_info:
            print(f"Lỗi: {user_info['error']}")
            return
        
        tag_name = user_info["name"]
        
        try:
            with open("nhaychet.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"l đọc file nhay.txt: {str(e)}")
            return
        
        if not lines:
            print("file nhay.txt trống")
            return
        
        line_index = 0
        while True:
            if line_index >= len(lines):
                line_index = 0
            
            message = lines[line_index].strip()
            if message:
                result = self.create_post(message, tag_id, tag_name)
                status = "Success" if result else "Failed"
                print(f"{self.uppost_count} | Mention: {tag_id} | Nội Dung: {message} | Trạng Thái: {status}")
            
            line_index += 1
            
            delay = random.uniform(5, 8)
            time.sleep(delay)


def main():
    print("Nhập cookie:")
    cookie = input().strip()
    
    print("Nhập id muốn tag:")
    tag_id = input().strip()
    
    poster = FacebookPoster(cookie)
    poster.run(tag_id)


if __name__ == "__main__":
    main()