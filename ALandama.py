import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)

# Состояния разговора
(
    CHOOSING_FORMAT,
    CHOOSING_CONSULTATION_MODE,
    ENTER_NAME,
    ENTER_AGE_CLASS,
    CHOOSING_PROBLEM,
    ENTERING_PROBLEM_DETAILS,
    CHOOSING_TIME,
    IN_DIALOGUE,
) = range(8)

class ClientBot:
    def __init__(self):
        self.psychologist = {
            "name": "Айдана Қабидуллақызы",
            "class": "Қазақ сыныптары",
            "id": "380587668"  # Замените на реальный ID психолога
        }
        self.active_dialogues = {}
        self.messages = {
            "welcome": "«ALandama» психологиялық қолдау қызметіне қош келдің! 🌟",
            "bot_description": "Мен саған мектеп психологына онлайн немесе офлайн жазылуға көмектесемін. Бірге шешім табамыз! 💫",
            "choose_format": "Алдымен танысып алайық! Әлде сұрағыңды анонимді түрде қойғың келе ме? 🤗",
            "with_name": "Таныстыру ✨",
            "anonymous": "Анонимді қалу ",
            "enter_name": "Алдымен танысып алайық! Сенің есімің кім? 🌟",
            "enter_age_class": "Жасың нешеде, нешінші сыныпта оқисың? 📚",
            "describe_situation": "Жақсы, жағдайды қысқаша сипаттап бере аласың ба?",
            "choose_time": "Саған қай күні, қай уақытта келу ыңғайлы болады? 📅",
            "thanks": "Сенімің үшін рақмет! ❤️\n{} сенімен жақын арада байланысады. Егер тағы да сұрақтарың болса, кез келген уақытта жаза аласың! 😊",
            "choose_consultation_mode": "Кеңесті қалай алғың келеді? 💭",
            "offline": "Жеке кездесуге жазылу 🤝",
            "online": "Онлайн кеңес алу 💻",
            "what_bothers": "Сені қандай мәселе мазалайды?",
            "problems": [
                "1️⃣ Оқу мен сабақтарға байланысты қиындықтар 📚",
                "2️⃣ Достарыммен немесе сыныптастарыммен қарым-қатынас 🤝",
                "3️⃣ Ата-анаммен түсініспеушіліктер 🏡",
                "4️⃣ Өзіме сенімсіздік, көңіл-күйімнің өзгеруі 💭",
                "5️⃣ Буллинг/Кибербуллинг",
                "6️⃣ Басқа нәрсе (өзің жаза аласың) ✍️"
            ],
            "use_end": "Диалогты аяқтау үшін /end командасын қолданыңыз.",
            "dialog_not_started": "Диалог әлі басталған жоқ немесе аяқталды.\nЖаңа диалогты бастау үшін /start қолданыңыз.",
            "dialog_ended": "Диалог аяқталды. Өтініш бергеніңіз үшін рахмет!\nЖаңа диалогты бастау үшін /start қолданыңыз.",
            "psychologist_accepted": "✅ Психолог сіздің өтінішіңізді қабылдады. Енді сөйлесе аласыз.",
            "request_postponed": "⏳ Сіздің өтінішіңіз уақытша кейінге қалдырылды. Психолог сізбен кейінірек байланысады."
        }

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the conversation."""
        context.user_data.clear()
        
        # Отправляем приветственное сообщение с выбором режима консультации
        keyboard = [
            [self.messages["offline"]],
            [self.messages["online"]]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await update.message.reply_text(
            "Сәлем! «ALandama» қосымшасына қош келдің! Мен – мектеп психологының көмекші чат-ботымын. "
            "Сенің сұрақтарыңа жауап беріп, мектеп психологы - Айдана Қабидуллақызына жазылуға көмектесе аламын ✨\n\n"
            f"{self.messages['choose_consultation_mode']}",
            reply_markup=reply_markup
        )
        return CHOOSING_CONSULTATION_MODE

    async def choose_consultation_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        context.user_data['consultation_mode'] = text
        
        if text == self.messages["offline"]:
            await update.message.reply_text(
                self.messages["enter_name"],
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTER_NAME
        else:
            keyboard = [
                [self.messages["anonymous"]],
                [self.messages["with_name"]]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                self.messages["choose_format"],
                reply_markup=reply_markup
            )
            return CHOOSING_FORMAT

    async def choose_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle format selection."""
        text = update.message.text

        if text == self.messages["with_name"]:
            # Если пользователь выбрал представиться
            await update.message.reply_text(
                self.messages["enter_name"],
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTER_NAME
        else:
            # Если пользователь выбрал анонимность
            context.user_data['name'] = "Анонимді"
            
            # Сразу переходим к выбору проблемы
            keyboard = [
                [problem] for problem in self.messages["problems"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            await update.message.reply_text(
                self.messages["what_bothers"],
                reply_markup=reply_markup
            )
            return CHOOSING_PROBLEM

    async def enter_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle name input."""
        context.user_data['name'] = update.message.text
        
        await update.message.reply_text(
            self.messages["enter_age_class"],
            reply_markup=ReplyKeyboardRemove()
        )
        return ENTER_AGE_CLASS

    async def enter_age_class(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle age and class input."""
        context.user_data['age_class'] = update.message.text
        
        keyboard = []
        for problem in self.messages["problems"]:
            keyboard.append([problem])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            self.messages["what_bothers"],
            reply_markup=reply_markup
        )
        return CHOOSING_PROBLEM

    async def choose_problem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['problem'] = update.message.text
        await update.message.reply_text(
            self.messages["describe_situation"],
            reply_markup=ReplyKeyboardRemove()
        )
        return ENTERING_PROBLEM_DETAILS

    async def enter_problem_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['problem_details'] = update.message.text
        
        if context.user_data['consultation_mode'] == self.messages["offline"]:
            await update.message.reply_text(
                self.messages["choose_time"]
            )
            return CHOOSING_TIME
        else:
            return await self.finish_conversation(update, context)

    async def choose_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['preferred_time'] = update.message.text
        return await self.finish_conversation(update, context)

    async def finish_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        client_id = update.effective_user.id

        message = (
            f"Жаңа өтініш!\n\n"
            f"Кеңес түрі: {context.user_data.get('consultation_mode')}\n"
            f"Оқушының аты: {context.user_data.get('name', 'Анонимді')}\n"
            f"Жасы/сыныбы: {context.user_data.get('age_class', 'Көрсетілмеген')}\n"
            f"Мәселе түрі: {context.user_data.get('problem')}\n"
            f"Толығырақ: {context.user_data.get('problem_details')}\n"
            f"Ыңғайлы уақыты: {context.user_data.get('preferred_time', 'Көрсетілмеген')}\n"
            f"Оқушының ID: {client_id}"
        )

        keyboard = [
            [
                InlineKeyboardButton("Қабылдау", callback_data=f"accept_{client_id}"),
                InlineKeyboardButton("Кейінге қалдыру", callback_data=f"postpone_{client_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                chat_id=self.psychologist['id'],
                text=message,
                reply_markup=reply_markup
            )
            self.active_dialogues[client_id] = {
                'psychologist_id': self.psychologist['id'],
                'state': 'pending'
            }
            await update.message.reply_text(
                self.messages['thanks'].format(self.psychologist['name'])
            )
        except Exception as e:
            logging.error(f"Failed to send message to psychologist: {e}")
            await update.message.reply_text(
                "Психологқа хабар жіберу кезінде қате пайда болды. Қайталап көріңіз."
            )
            return ConversationHandler.END

        return IN_DIALOGUE

    async def accept_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        client_id = int(query.data.split("_")[1])
        
        if client_id in self.active_dialogues:
            self.active_dialogues[client_id]['state'] = 'active'
            
            await context.bot.edit_message_reply_markup(
                chat_id=query.message.chat_id,
                message_id=query.message.message_id,
                reply_markup=None
            )
            
            # Сообщение для психолога
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ Диалог басталды. Диалогты аяқтау үшін /end қолданыңыз."
            )

            # Сообщение для клиента
            await context.bot.send_message(
                chat_id=client_id,
                text=self.messages["psychologist_accepted"]
            )

    async def postpone_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        client_id = int(query.data.split("_")[1])
        
        await context.bot.edit_message_reply_markup(
            chat_id=query.message.chat_id,
            message_id=query.message.message_id,
            reply_markup=None
        )
        
        # Сообщение для психолога
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⏳ Өтініш кейінге қалдырылды. Оған кейінірек орала аласыз."
        )

        # Сообщение для клиента
        await context.bot.send_message(
            chat_id=client_id,
            text=self.messages["request_postponed"]
        )

    async def end_dialogue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /end command - only available for psychologists."""
        user_id = update.effective_user.id
        
        # Проверяем, является ли пользователь психологом
        is_psychologist = str(user_id) == self.psychologist['id']
        
        if is_psychologist:
            # Если это психолог, позволяем завершить диалог
            for client_id, dialogue in self.active_dialogues.items():
                if dialogue['psychologist_id'] == str(user_id):
                    await self.close_dialogue(context, client_id, str(user_id))
            return ConversationHandler.END
        else:
            # Если это клиент, отправляем сообщение что команда недоступна
            await update.message.reply_text(
                "Диалогты тек психолог қана аяқтай алады."
            )
            return IN_DIALOGUE

    async def close_dialogue(self, context, client_id, psychologist_id):
        if client_id in self.active_dialogues:
            del self.active_dialogues[client_id]
            
            await context.bot.send_message(
                chat_id=client_id,
                text=self.messages["dialog_ended"]
            )
            await context.bot.send_message(
                chat_id=psychologist_id,
                text=f"Оқушымен диалог аяқталды {client_id}."
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message_text = update.message.text

        if message_text.startswith('/'):
            return

        is_psychologist = str(user_id) == self.psychologist['id']

        if is_psychologist:
            active_client = None
            for client_id, dialogue in self.active_dialogues.items():
                if dialogue['psychologist_id'] == str(user_id) and dialogue['state'] == 'active':
                    active_client = client_id
                    break
                    
            if active_client:
                await context.bot.send_message(
                    chat_id=active_client,
                    text=f"Психолог: {message_text}"
                )
            else:
                await update.message.reply_text(
                    "Оқушылармен белсенді диалогтар жоқ.\n"
                    "Диалогты бастау үшін оқушының өтінішін қабылдаңыз."
                )
        else:
            if user_id in self.active_dialogues and self.active_dialogues[user_id]['state'] == 'active':
                psychologist_id = self.active_dialogues[user_id]['psychologist_id']
                await context.bot.send_message(
                    chat_id=psychologist_id,
                    text=f"Оқушы {user_id}: {message_text}"
                )
            else:
                await update.message.reply_text(
                    self.messages["dialog_not_started"]
                )

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    bot = ClientBot()
    application = Application.builder().token("8069846201:AAGkz7v0imc9Er_mxd3FT_X2Eu_cg3rADa4").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', bot.start)],
        states={
            CHOOSING_CONSULTATION_MODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.choose_consultation_mode)
            ],
            CHOOSING_FORMAT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.choose_format)
            ],
            ENTER_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.enter_name)
            ],
            ENTER_AGE_CLASS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.enter_age_class)
            ],
            CHOOSING_PROBLEM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.choose_problem)
            ],
            ENTERING_PROBLEM_DETAILS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.enter_problem_details)
            ],
            CHOOSING_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.choose_time)
            ],
            IN_DIALOGUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message)
            ]
        },
        fallbacks=[CommandHandler('end', bot.end_dialogue)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(bot.accept_request, pattern="^accept_"))
    application.add_handler(CallbackQueryHandler(bot.postpone_request, pattern="^postpone_"))
    application.add_handler(CommandHandler('end', bot.end_dialogue))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))

    print("Бот іске қосылды...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
