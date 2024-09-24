import asyncio
from pywebio import start_server
from pywebio.input import input, input_group, actions
from pywebio.output import put_markdown, put_scrollable, put_buttons, output, toast
from pywebio.session import run_async

chat_msgs = []
online_users = set()
MAX_MESSAGES_COUNT = 100

async def display_welcome(msg_box):
    put_markdown("## 🧊 Xush kelibsiz onlayn chatga!\nUshbu chatning kod manzili 100 qator kodni tashkil etadi!")
    msg_box.append(put_markdown("Bu yerda siz boshqa foydalanuvchilar bilan muloqot qilishingiz mumkin."))

async def handle_user_input(nickname, msg_box):
    while True:
        data = await input_group("💭 Yangi xabar", [
            input(placeholder="Xabar matni ...", name="msg"),
            actions(name="cmd", buttons=["Yuborish", {'label': "Chatdan chiqish", 'type': 'cancel'}])
        ], validate=lambda m: ('msg', "Iltimos, xabar matnini kiriting!") if m["cmd"] == "Yuborish" and not m['msg'] else None)

        if data is None:  # Foydalanuvchi chiqish tanladi
            break

        msg_box.append(put_markdown(f"`{nickname}`: {data['msg']}"))
        chat_msgs.append((nickname, data['msg']))

async def refresh_messages(nickname, msg_box):
    global chat_msgs
    last_idx = len(chat_msgs)

    while True:
        await asyncio.sleep(1)
        
        for m in chat_msgs[last_idx:]:
            if m[0] != nickname:  # Agar xabar joriy foydalanuvchidan kelmasa
                msg_box.append(put_markdown(f"`{m[0]}`: {m[1]}"))

        if len(chat_msgs) > MAX_MESSAGES_COUNT:
            chat_msgs[:] = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)

async def main():
    global chat_msgs

    msg_box = output()
    put_scrollable(msg_box, height=300, keep_bottom=True)
    
    await display_welcome(msg_box)

    nickname = await input("Chatga kirish", required=True, placeholder="Ismingiz",
                           validate=lambda n: "Bu nick allaqachon ishlatilmoqda!" if n in online_users or n == '📢' else None)
    online_users.add(nickname)

    chat_msgs.append(('📢', f'`{nickname}` chatga qo\'shildi!'))
    msg_box.append(put_markdown(f'📢 `{nickname}` chatga qo\'shildi'))

    refresh_task = run_async(refresh_messages(nickname, msg_box))
    await handle_user_input(nickname, msg_box)

    refresh_task.close()
    online_users.remove(nickname)
    toast("Siz chatdan chiqdingiz!")
    msg_box.append(put_markdown(f'📢 Foydalanuvchi `{nickname}` chatdan chiqdi!'))

    put_buttons(['Qaytadan kirish'], onclick=lambda btn: run_js('window.location.reload()'))

if __name__ == "__main__":
    start_server(main, debug=True, port=8080, cdn=False)
