from flask import Flask, request
import requests
import cloudinary
import cloudinary.uploader
from PIL import Image
import io

app = Flask(__name__)

# 🔑 ใส่ของคุณ
CHANNEL_ACCESS_TOKEN = "EJAWE8x7YodPqyYxyBYhicZX8i5N9rWZC+pogtrRhBYmFtfEdHdI3+0YS+8kpWLBnx5tOPz+tWzrn693mTF5K6m5Z30fgdowDfvfAl1ACitJE27aYRyV3os4ZjOZ17tCnzH1w0yEAPT3AkrE4mYCmgdB04t89/1O/w1cDnyilFU="

cloudinary.config(
    cloud_name="ddr1jxzrr",
    api_key="685973871719362",
    api_secret="bOb42Auph9wkuhCAu_Ry75m8yY0"
)

user_images = {}

# -------------------------
# โหลดรูปจาก LINE
# -------------------------
def get_image_content(message_id):
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"
    headers = {"Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers)
    return r.content

# -------------------------
# upload Cloudinary
# -------------------------
def upload_to_cloudinary(image_bytes):
    result = cloudinary.uploader.upload(image_bytes)
    return result["secure_url"]

# -------------------------
# crop รูปให้พอดีช่อง
# -------------------------
def fit_image(img, w, h):
    img_ratio = img.width / img.height
    box_ratio = w / h

    if img_ratio > box_ratio:
        new_height = img.height
        new_width = int(box_ratio * new_height)
    else:
        new_width = img.width
        new_height = int(new_width / box_ratio)

    left = (img.width - new_width) // 2
    top = (img.height - new_height) // 2

    img = img.crop((left, top, left + new_width, top + new_height))
    return img.resize((w, h))

# -------------------------
# รวมรูปลง template
# -------------------------
def create_collage(image_urls):
    # ใช้ template ของคุณ
    canvas = Image.open("template.png").convert("RGB")

    # 📐 layout อิงจากงานคุณ (8 ช่อง)
    layouts = {
        8: [
            (60, 120, 200, 220), (280, 120, 200, 220),
            (500, 120, 200, 220), (720, 120, 200, 220),

            (60, 360, 200, 220), (280, 360, 200, 220),
            (500, 360, 200, 220), (720, 360, 200, 220),
        ],
        6: [
            (100,150,250,220),(375,150,250,220),(650,150,250,220),
            (100,380,250,220),(375,380,250,220),(650,380,250,220),
        ],
        4: [
            (120,150,350,220),(530,150,350,220),
            (120,380,350,220),(530,380,350,220),
        ]
    }

    layout = layouts.get(len(image_urls), layouts[4])

    for i, url in enumerate(image_urls[:len(layout)]):
        response = requests.get(url)
        img = Image.open(io.BytesIO(response.content))

        x, y, w, h = layout[i]
        img = fit_image(img, w, h)

        canvas.paste(img, (x, y))

    # save ลง memory
    buffer = io.BytesIO()
    canvas.save(buffer, format="JPEG")
    buffer.seek(0)

    return buffer

# -------------------------
# webhook
# -------------------------
@app.route("/", methods=["POST"])
def webhook():
    body = request.json

    for event in body.get("events", []):
        if event["type"] != "message":
            continue

        reply_token = event["replyToken"]
        user_id = event["source"]["userId"]
        message = event["message"]

        # 📸 รับรูป
        if message["type"] == "image":
            message_id = message["id"]

            try:
                image_content = get_image_content(message_id)
                image_url = upload_to_cloudinary(image_content)

                user_images.setdefault(user_id, []).append(image_url)

                reply_msg = {
                    "type": "text",
                    "text": "รับรูปแล้ว 👍"
                }

            except Exception as e:
                print("ERROR:", e)
                reply_msg = {
                    "type": "text",
                    "text": "อัปโหลดรูปไม่สำเร็จ"
                }

        # 💬 ข้อความ
        elif message["type"] == "text":
            text = message["text"]

            if text == "สร้าง":
                images = user_images.get(user_id, [])

                if not images:
                    reply_msg = {
                        "type": "text",
                        "text": "ยังไม่มีรูป ส่งรูปมาก่อน"
                    }
                else:
                    try:
                        collage_buffer = create_collage(images)
                        result = cloudinary.uploader.upload(collage_buffer)
                        collage_url = result["secure_url"]

                        reply_msg = {
                            "type": "image",
                            "originalContentUrl": collage_url,
                            "previewImageUrl": collage_url
                        }

                        user_images[user_id] = []

                    except Exception as e:
                        print("COLLAGE ERROR:", e)
                        reply_msg = {
                            "type": "text",
                            "text": "สร้างรูปไม่สำเร็จ"
                        }

            elif text == "ล้าง":
                user_images[user_id] = []
                reply_msg = {
                    "type": "text",
                    "text": "ล้างรูปแล้ว"
                }

            else:
                reply_msg = {
                    "type": "text",
                    "text": "ส่งรูป แล้วพิมพ์ 'สร้าง'"
                }

        else:
            continue

        # reply
        requests.post(
            "https://api.line.me/v2/bot/message/reply",
            headers={
                "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "replyToken": reply_token,
                "messages": [reply_msg]
            }
        )

    return "OK"