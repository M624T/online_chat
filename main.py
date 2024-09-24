import asyncio
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import run_async, run_js, set_env
from collections import deque

# Doimiy qiymat
MAX_MESSAGES_COUNT = 100

# Global holat
chat_msgs = deque(maxlen=MAX_MESSAGES_COUNT)
online_users = set()

async def main():
    global chat_msgs

    # PyWebIO muhitini sozlash (avtomatik qayta ulanish funksiyasini o'chirish)
    set_env(title="Chat Ilovasi", auto_scroll_bottom=True, output_max_length=100)
    
    # Xush kelibsiz xabari
    put_markdown("## 🧊 Onlayn chatga xush kelibsiz!\nUshbu chat 100 ta kod satrida amalga oshirilgan!")
    msg_box = output()
    put_scrollable(msg_box, height=300, keep_bottom=True)

    # Foydalanuvchi allaqachon kirganmi, tekshirish (sessiya boshqaruvi)
    nickname = session_info.user_agent.split()[0] if session_info.user_agent else None
    if nickname and nickname not in online_users:
        online_users.add(nickname)
        add_chat_message('📢', f'`{nickname}` chatga qayta qo\'shildi!')
        msg_box.append(put_markdown(f'📢 `{nickname}` chatga qayta qo\'shildi!'))
    else:
        # Foydalanuvchi kiritilishi va ismi unikal bo'lishi kerakligini tekshirish
        nickname = await input("Chatga kiring", required=True, placeholder="Ismingiz",
                               validate=validate_nickname)
        online_users.add(nickname)
        run_js(f'window.sessionStorage.setItem("nickname", "{nickname}")')  # Ismni sessiyada saqlash

        # Boshqalarga foydalanuvchi qo'shilgani haqida xabar berish
        add_chat_message('📢', f'`{nickname}` chatga qo\'shildi!')
        msg_box.append(put_markdown(f'📢 `{nickname}` chatga qo\'shildi!'))

    # Xabar qutisini fon rejimida yangilab turish
    refresh_task = run_async(refresh_messages(nickname, msg_box))

    while True:
        # Foydalanuvchi yangi xabar yozishi uchun kiritish maydoni
        data = await input_group("💬 Yangi xabar", [
            input(placeholder="Xabar...", name="msg"),
            actions(name="cmd", buttons=["Yuborish", {'label': "Chatni tark etish", 'type': 'cancel'}])
        ], validate=validate_message)

        if data is None:
            break

        # Xabarni chatga qo'shish
        add_chat_message(nickname, data['msg'])
        msg_box.append(put_markdown(f"`{nickname}`: {data['msg']}"))

    # Foydalanuvchi chiqib ketganda fon vazifasini to'xtatish va tozalash
    refresh_task.close()

    online_users.remove(nickname)
    toast("Siz chatdan chiqdingiz!")
    add_chat_message('📢', f'`{nickname}` chatni tark etdi!')
    msg_box.append(put_markdown(f'📢 `{nickname}` chatni tark etdi!'))

    # Chatga qayta kirish imkoniyati
    put_buttons(['Qayta kirish'], onclick=lambda btn: run_js('window.location.reload()'))


async def refresh_messages(nickname, msg_box):
    last_idx = len(chat_msgs)
    
    while True:
        await asyncio.sleep(1)

        # Boshqa foydalanuvchilarning yangi xabarlarini ko'rsatish
        for m in list(chat_msgs)[last_idx:]:
            if m[0] != nickname:
                msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}`"))
        
        last_idx = len(chat_msgs)

def add_chat_message(sender, message):
    """ Global chat ro'yxatiga xabar qo'shish """
    chat_msgs.append((sender, message))

def validate_nickname(nickname):
    """ Foydalanuvchi ismi unikal va rezerv qilinmaganligini tekshirish """
    if nickname in online_users or nickname == '📢':
        return "Bu ism allaqachon ishlatilgan!"
    return None

def validate_message(data):
    """ Xabar bo'sh emasligini tekshirish """
    if data["cmd"] == "Yuborish" and not data['msg']:
        return ('msg', "Xabarni kiriting!")
    return None

if __name__ == "__main__":
    start_server(main, debug=True, port=8080, cdn=False)
