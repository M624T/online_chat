import asyncio

from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.session import defer_call, info as session_info, run_async

MAX_MESSAGES_CNT = 10 ** 4

chat_msgs = []  # Chatdagi xabarlar tarixi. Har bir element (ism, xabar matni)
online_users = set()  # Onlayn foydalanuvchilar to'plami


def t(uzb, rus, eng):
    """Foydalanuvchi brauzeri tiliga qarab o'zbek, rus yoki ingliz tilidagi matnni qaytaradi"""
    if 'ru' in session_info.user_language:
        return rus
    elif 'uz' in session_info.user_language:
        return uzb
    else:
        return eng


async def refresh_msg(my_name):
    """Joriy sessiyaga yangi xabarlarni yuborish"""
    global chat_msgs
    last_idx = len(chat_msgs)
    while True:
        await asyncio.sleep(0.5)
        for m in chat_msgs[last_idx:]:
            if m[0] != my_name:  # Faqat boshqa foydalanuvchilar yuborgan xabarlarni yangilash
                put_markdown('`%s`: %s' % m, sanitize=True, scope='msg-box')

        # Eski xabarlarni o'chirish
        if len(chat_msgs) > MAX_MESSAGES_CNT:
            chat_msgs = chat_msgs[len(chat_msgs) // 2:]

        last_idx = len(chat_msgs)


async def main():
    """PyWebIO chat xonasi

    Bu yerda hozir onlayn bo'lganlar bilan chat qilishingiz mumkin.
    """
    global chat_msgs

    put_markdown(t("## PyWebIO chat xonasi\nChatga xush kelibsiz! Siz bu yerda hozir onlayn bo'lgan barcha odamlar bilan suhbatlashishingiz mumkin. Ushbu sahifani brauzeringizning bir nechta oynalarida ochib, ko'p foydalanuvchi muhitini sinab ko'rishingiz mumkin. Bu dastur 100 ta kod satridan kamroq yozilgan, kod manbasi [bu yerda](https://github.com/wang0618/PyWebIO/blob/dev/demos/chat_room.py)",
                   "## PyWebIO чат\nДобро пожаловать в чат! Вы можете общаться со всеми, кто сейчас онлайн. Вы можете открыть эту страницу в нескольких вкладках браузера, чтобы имитировать многопользовательскую среду. Приложение написано менее чем на 100 строках кода, исходный код доступен [здесь](https://github.com/wang0618/PyWebIO/blob/dev/demos/chat_room.py)",
                   "## PyWebIO chat room\nWelcome to the chat room, you can chat with all the people currently online. You can open this page in multiple tabs of your browser to simulate a multi-user environment. This application uses less than 100 lines of code, the source code is [here](https://github.com/wang0618/PyWebIO/blob/dev/demos/chat_room.py)"))

    put_scrollable(put_scope('msg-box'), height=300, keep_bottom=True)
    nickname = await input(t("Ismingiz", "Ваше имя", "Your nickname"), required=True, validate=lambda n: t('Bu ism allaqachon ishlatilgan', 'Это имя уже используется', 'This name is already been used') if n in online_users or n == '📢' else None)

    online_users.add(nickname)

    # Sessiya ochilishidan oldin xabarni olish uchun qo'shilgan qism
    leave_message = t('`%s` chatni tark etdi. Hozir %s foydalanuvchi onlayn' % (nickname, len(online_users)),
                      '`%s` покинул чат. Сейчас онлайн %s пользователей' % (nickname, len(online_users)),
                      '`%s` leaves the room. %s users currently online' % (nickname, len(online_users)))

    chat_msgs.append(('📢', t('`%s` chatga qo\'shildi. Hozir %s foydalanuvchi onlayn' % (nickname, len(online_users)),
                              '`%s` присоединился к чату. Сейчас онлайн %s пользователей' % (nickname, len(online_users)),
                              '`%s` joins the room. %s users currently online' % (nickname, len(online_users)))))
    put_markdown(t('`📢`: `%s` chatga qo\'shildi. Hozir %s foydalanuvchi onlayn' % (nickname, len(online_users)),
                  '`📢`: `%s` присоединился к чату. Сейчас онлайн %s пользователей' % (nickname, len(online_users)),
                  '`📢`: `%s` joins the room. %s users currently online' % (nickname, len(online_users))), sanitize=True, scope='msg-box')

    @defer_call
    def on_close():
        online_users.remove(nickname)
        chat_msgs.append(('📢', leave_message))  # Faqat oldindan saqlangan xabarni qo'shish

    refresh_task = run_async(refresh_msg(nickname))

    while True:
        data = await input_group(t('Xabar yuboring', 'Отправить сообщение', 'Send message'), [
            input(name='msg', help_text=t('Xabar matni Markdown sintaksisini qo\'llab-quvvatlaydi', 'Содержание сообщения поддерживает синтаксис Markdown', 'Message content supports inline Markdown syntax')),
            actions(name='cmd', buttons=[t('Yuborish', 'Отправить', 'Send'), t('Ko\'p qatorli kiritish', 'Многострочный ввод', 'Multiline Input'), {'label': t('Chiqish', 'Выход', 'Exit'), 'type': 'cancel'}])
        ], validate=lambda d: ('msg', t('Xabar matni bo\'sh bo\'lmasligi kerak', 'Сообщение не должно быть пустым', 'Message content cannot be empty')) if d['cmd'] == t('Yuborish', 'Отправить', 'Send') and not d['msg'] else None)

        if data is None:
            break
        if data['cmd'] == t('Ko\'p qatorli kiritish', 'Многострочный ввод', 'Multiline Input'):
            data['msg'] = '\n' + await textarea(t('Xabar matni', 'Содержание сообщения', 'Message content'), help_text=t('Xabar matni Markdown sintaksisini qo\'llab-quvvatlaydi', 'Содержание сообщения поддерживает синтаксис Markdown', 'Message content supports Markdown syntax'))
        
        put_markdown('`%s`: %s' % (nickname, data['msg']), sanitize=True, scope='msg-box')
        chat_msgs.append((nickname, data['msg']))

    refresh_task.close()
    toast(t("Siz chatdan chiqdiz!", "Вы вышли из чата", "You have left the chat room"))


if __name__ == '__main__':
    start_server(main, debug=True, port=8080)
