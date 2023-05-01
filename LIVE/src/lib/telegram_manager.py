from datetime import datetime
import telegram
import asyncio
import src.lib.utils as utils
import src.global_variables as global_variables

class TelegramManager():

    def __init__(self, token=global_variables.telegram_token):
        self.token = token

    def send_msg(self, msg):
        self.msg = str(msg)
        try:
            asyncio.run(self.send_msg_to_telegram())
        except Exception as e:
            utils.debug(2, "Telegram Error")
            utils.debug(3, e)

    async def send_msg_to_telegram(self):
        bot = telegram.Bot(token=self.token)
        updates = await bot.get_updates()
        chat_id = updates[-1].message.chat_id
        await bot.send_message(chat_id=chat_id, text=self.msg)
