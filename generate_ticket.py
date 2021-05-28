#!/usr/bin/env python 3
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup

TEMPLATE_PATH = 'files/ticket_base.png'  # here's your base_image, you may use different one
FONT_PATH = 'files/Roboto-Thin.ttf'
FONT_SIZE = 20
BLACK = (0, 0, 0, 255)

NAME_POS = (300, 150)
EMAIL_POS = (300, 215)

AVATAR_SIZE = 100
AVATAR_POS = (70, 100)


def generate_ticket(name, email):
    base = Image.open(fp=TEMPLATE_PATH).convert('RGBA')
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    draw = ImageDraw.Draw(im=base)
    draw.text(NAME_POS, name, font=font, fill=BLACK)
    draw.text(EMAIL_POS, email, font=font, fill=BLACK)

    response = requests.get(url=f'https://api.multiavatar.com/{email}.png')
    avatar_file_like = BytesIO(response.content)  # make bytes file-like object
    avatar = Image.open(fp=avatar_file_like)
    (width, height) = (avatar.width // 4, avatar.height // 4)
    resized_avatar = avatar.resize((width, height))

    base.paste(resized_avatar, AVATAR_POS)  # paste avatar img on base img

    temp_file = BytesIO()
    base.save(temp_file, 'png')
    temp_file.seek(0)

    return temp_file


generate_ticket(name='name', email='email@email.com')
