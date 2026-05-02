from flask import Flask, request
import requests
import os

app = Flask(__name__)

CHANNEL_ACCESS_TOKEN = "EJAWE8x7YodPqyYxyBYhicZX8i5N9rWZC+pogtrRhBYmFtfEdHdI3+0YS+8kpWLBnx5tOPz+tWzrn693mTF5K6m5Z30fgdowDfvfAl1ACitJE27aYRyV3os4ZjOZ17tCnzH1w0yEAPT3AkrE4mYCmgdB04t89/1O/w1cDnyilFU="

# ดึงรูปจาก LINE
def get_image_content(message_id):
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    r = requests.get(url, headers=headers)
    return r.content

# webhook
@app.route("/", methods=["POST"])
def webhook():
    body = request.json

    for event in body.get("events", []):
        if event["type"] != "message":
            continue

        reply_token = event["replyToken"]
        message = event["message"]

        # 📸 ถ้าเป็นรูป
        if message["type"] == "image":
            message_id = message["id"]

            # ดึง binary รูปมา
            image_content = get_image_content(message_id)

            image_url = upload_to_imgur(image_content)

            data = {
                "replyToken": reply_token,
                "messages": [
                {
                        "type": "image",
                        "originalContentUrl": image_url,
                        "previewImageUrl": image_url
                }
                ]
            }

            requests.post(url, headers=headers, json=data)    

        # 💬 ถ้าเป็น text
        elif message["type"] == "text":
            text = message["text"]

            url = "https://api.line.me/v2/bot/message/reply"
            headers = {
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }

            data = {
                "replyToken": reply_token,
                "messages": [
                    {
                        "type": "text",
                        "text": f"คุณพิมพ์ว่า: {text}"
                    }
                ]
            }

            requests.post(url, headers=headers, json=data)

    return "OK"

def upload_to_imgur(image_bytes):
    url = "https://api.imgur.com/3/image"
    headers = {
        "Authorization": "Client-ID YOUR_CLIENT_ID"
    }

    files = {
        "image": image_bytes
    }

    response = requests.post(url, headers=headers, files=files)
    return response.json()["data"]["link"]
