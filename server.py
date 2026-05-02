from flask import Flask, request
import requests
import cloudinary
import cloudinary.uploader
from PIL import Image, ImageDraw
import io
import math

app = Flask(__name__)

# 🔑 ใส่ของคุณ
CHANNEL_ACCESS_TOKEN = "EJAWE8x7YodPqyYxyBYhicZX8i5N9rWZC+pogtrRhBYmFtfEdHdI3+0YS+8kpWLBnx5tOPz+tWzrn693mTF5K6m5Z30fgdowDfvfAl1ACitJE27aYRyV3os4ZjOZ17tCnzH1w0yEAPT3AkrE4mYCmgdB04t89/1O/w1cDnyilFU="

cloudinary.config(
    cloud_name="ddr1jxzrr",
    api_key="685973871719362",
    api_secret="bOb42Auph9wkuhCAu_Ry75m8yY0"
)

# เก็บรูป user
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
# สร้าง grid อัตโนมัติ
# -------------------------
def generate_grid(n, canvas_w, canvas_h, margin=20, gap=15):
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    cell_w = (canvas_w - margin*2 - gap*(cols-1)) // cols
    cell_h = (canvas_h - margin*2 - gap*(rows-1)) // rows

    positions = []

    for i in range(n):
        row = i // cols
        col = i % cols

        x = margin + col * (cell_w + gap)
        y = margin + row * (cell_h + gap)

        positions.append((x, y, cell_w, cell_h))

    return positions

# -------------------------
# รวมรูป + แถบแดง
# -------------------------
def create_collage(image_urls):
    canvas_w, canvas_h = 1000, 1000

    header_h = 68
    footer_h = 86

    canvas = Image.open("template.png").convert("RGB")
    canvas_w, canvas_h = canvas.size

    content_y = header_h
    content_h = canvas_h - header_h - footer_h

    positions = generate_grid(len(image_urls), canvas_w, content_h)

    for i, url in enumerate(image_urls):
        response = requests.get(url)
        img = Image.open(io.BytesIO(response.content)).convert("RGB")

        x, y, w, h = positions[i]
        y = y + content_y

        img = fit_image(img, w, h)
        canvas.paste(img, (x, y))

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
                result = cloudinary.uploader.upload(image_content)
                image_url = result["secure_url"]

                user_images.setdefault(user_id, []).append(image_url)

                reply_msg = {
                    "type": "text",
                    "text": "รับรูปแล้ว 👍 ส่งเพิ่มได้ หรือพิมพ์ 'สร้าง'"
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

        # 🔁 reply
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