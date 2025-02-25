import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove, InputMediaPhoto
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
    CHOOSING_LANGUAGE,
    CHOOSING_PSYCHOLOGIST,
    CHOOSING_FORMAT,
    CHOOSING_CONSULTATION_MODE,
    ENTER_NAME,
    ENTER_AGE_CLASS,
    CHOOSING_PROBLEM,
    ENTERING_PROBLEM_DETAILS,
    CHOOSING_TIME,
    IN_DIALOGUE,
) = range(10)

class ClientBot:
    def __init__(self):
        self.psychologists = {
            "aidana": {
                "name": {"ru": "Айдана Кабидуллаевна", "kz": "Айдана Қабидуллақызы"},
                "class": {"ru": "Казахские классы", "kz": "Қазақ сыныптары"},
                "id": "380587668"
            },
            "dinara": {
                "name": {"ru": "Динара Талгатовна", "kz": "Динара Талғатқызы"},
                "class": {"ru": "Русские классы", "kz": "Орыс сыныптары"},
                "id": "740569027"
            }
        }
        self.active_dialogues = {}
        self.messages = {
            "ru": {
                "welcome": "Добро пожаловать в службу психологической поддержки «AISezim»! 🌟",
                "bot_description": "Я помогу тебе записаться к школьному психологу онлайн или офлайн. Вместе мы найдем решение! 💫",
                "choose_language": "На каком языке тебе удобнее общаться? 💭",
                "choose_format": "Давайте сначала познакомимся! Или вы хотите задать вопрос анонимно? 🤗",
                "with_name": "Представиться ✨",
                "anonymous": "Остаться анонимным ",
                "enter_name": "Как тебя зовут? 🌟",
                "enter_age_class": "Сколько тебе лет, в каком классе учишься? 📚",
                "describe_situation": "Хорошо, можешь кратко описать ситуацию?",
                "choose_time": "В какой день и время тебе будет удобнее прийти? 📅",
                "thanks": "Спасибо за доверие! ❤️\n{} свяжется с вами в ближайшее время. Если у вас появятся вопросы, не стесняйтесь писать в любое время! 😊",
                "choose_consultation_mode": "Как бы ты хотел(а) получить консультацию? 💭",
                "offline": "Записаться на личную встречу 🤝",
                "online": "Получить онлайн консультацию 💻",
                "choose_psychologist": "Хорошо!\n\nВыберите психолога в зависимости от вашего класса обучения:\n\n👩‍💼 Айдана Кабидуллакызы – психолог казахских классов\n👩‍💼 Динара Талгатовна – психолог русских классов",
                "enter_name_age": "Сколько тебе лет, в каком классе учишься? 😊",
                "what_bothers": "Какая проблема тебя беспокоит?",
                "problems": [
                    "1️⃣ Трудности с учебой и занятиями 📚",
                    "2️⃣ Отношения с друзьями или одноклассниками 🤝",
                    "3️⃣ Недопонимание с родителями 🏡",
                    "4️⃣ Неуверенность в себе, перепады настроения 💭",
                    "5️⃣ Буллинг/Кибербуллинг",
                    "6️⃣ Другое (можешь написать сам) ✍️"
                ],
                "enter_name_age": "Сколько тебе лет, в каком классе учишься? 😊",
                "use_end": "Используйте команду /end для завершения диалога когда будете готовы.",
                "dialog_not_started": "Диалог еще не начат или уже завершен.\nИспользуйте /start для начала нового диалога.",
                "dialog_ended": "Диалог завершен. Спасибо за обращение!\nИспользуйте /start чтобы начать новый диалог.",
                "psychologist_accepted": "✅ Психолог принял ваш запрос. Теперь вы можете общаться.",
                "request_postponed": "⏳ Ваш запрос временно отложен. Психолог свяжется с вами позже.",
                "select_button": "Выберите удобного для вас специалиста ⬇️",
            },
            "kz": {
                "welcome": "«AISezim» психологиялық қолдау қызметіне қош келдің! 🌟",
                "bot_description": "Мен саған мектеп психологына онлайн немесе офлайн жазылуға көмектесемін. Бірге шешім табамыз! 💫",
                "choose_language": "Қай тілде сөйлескің келеді? 💭",
                "choose_format": "Алдымен танысып алайық! Әлде сұрағыңды анонимді түрде қойғың келе ме? 🤗",
                "with_name": "Таныстыру ✨",
                "anonymous": "Анонимді қалу ",
                "enter_name": "Сенің есімің кім? 🌟",
                "enter_age_class": "Жасың нешеде, нешінші сыныпта оқисың? 📚",
                "describe_situation": "Жақсы, жағдайды қысқаша сипаттап бере аласың ба?",
                "choose_time": "Саған қай күні, қай уақытта келу ыңғайлы болады? 📅",
                "thanks": "Сенімің үшін рақмет! ❤️\n{} сенімен жақын арада байланысады. Егер тағы да сұрақтарың болса, кез келген уақытта жаза аласың! 😊",
                "choose_consultation_mode": "Кеңесті қалай алғың келеді? 💭",
                "offline": "Жеке кездесуге жазылу 🤝",
                "online": "Онлайн кеңес алу 💻",
                "choose_psychologist": "Жақсы!\n\nӨзің оқитын сыныбына байланысты психолог маманың таңда:\n\n👩‍💼 Айдана Қабидуллақызы – қазақ сыныптарының психологы\n👩‍💼 Динара Талғатқызы – орыс сыныптарының психологы",
                "enter_name_age": "Өтінемін, есімің мен жасыңды жаз:",
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
                "request_postponed": "⏳ Сіздің өтінішіңіз уақытша кейінге қалдырылды. Психолог сізбен кейінірек байланысады.",
                "select_button": "Өзіңе ыңғайлы маманды таңда ⬇️",
            }
        }

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the conversation and ask for language preference."""
        context.user_data.clear()
        
        keyboard = [
            [
                InlineKeyboardButton("Қазақша", callback_data="lang_kz"),
                InlineKeyboardButton("Русский", callback_data="lang_ru")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение
        await update.message.reply_text(
            "Сәлем! «AISezim» қосымшасына қош келдің! Мен – мектеп психологының көмекші чат-ботымын. "
            "Сенің сұрақтарыңа жауап беріп, мектеп психологына жазылуыңа көмектесе аламын ✨\n\n"
            "Привет! Добро пожаловать в приложение «AISezim»! Я – помощник школьного психолога. "
            "Помогу тебе записаться на консультацию и отвечу на твои вопросы ✨"
        )
        
        await update.message.reply_text(
            "Қай тілде сөйлескің келеді? / На каком языке продолжим? 💭",
            reply_markup=reply_markup
        )
        return CHOOSING_LANGUAGE

    async def choose_language(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language selection."""
        query = update.callback_query
        await query.answer()
        
        language = query.data.split('_')[1]
        context.user_data['language'] = language
        
        # Создаем клавиатуру для выбора психолога
        keyboard = [
            [
                InlineKeyboardButton(
                    f"{self.psychologists['aidana']['name'][language]}",
                    callback_data="psych_aidana"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{self.psychologists['dinara']['name'][language]}",
                    callback_data="psych_dinara"
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем сообщение с описанием и кнопками
        await query.message.edit_text(
            text=self.messages[language]["choose_psychologist"],
            reply_markup=reply_markup
        )

        return CHOOSING_PSYCHOLOGIST

    async def choose_psychologist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle psychologist selection."""
        query = update.callback_query
        await query.answer()
        
        language = context.user_data['language']
        psychologist_id = query.data.split('_')[1]
        context.user_data['psychologist'] = self.psychologists[psychologist_id]
        
        keyboard = [
            [self.messages[language]["offline"]],
            [self.messages[language]["online"]]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.messages[language]["choose_consultation_mode"],
            reply_markup=reply_markup
        )
        return CHOOSING_CONSULTATION_MODE

    async def choose_consultation_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        language = context.user_data['language']
        text = update.message.text
        context.user_data['consultation_mode'] = text
        
        if text == self.messages[language]["offline"]:
            await update.message.reply_text(
                self.messages[language]["enter_name"],
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTER_NAME
        else:
            keyboard = [
                [self.messages[language]["anonymous"]],
                [self.messages[language]["with_name"]]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
            await update.message.reply_text(
                self.messages[language]["choose_format"],
                reply_markup=reply_markup
            )
            return CHOOSING_FORMAT

    async def choose_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle format selection."""
        language = context.user_data['language']
        text = update.message.text

        if text == self.messages[language]["with_name"]:
            # Если пользователь выбрал представиться
            await update.message.reply_text(
                self.messages[language]["enter_name"],
                reply_markup=ReplyKeyboardRemove()
            )
            return ENTER_NAME
        else:
            # Если пользователь выбрал анонимность
            context.user_data['name'] = "Аноним" if language == "ru" else "Анонимді"
            
            # Сразу переходим к выбору проблемы
            keyboard = [
                [problem] for problem in self.messages[language]["problems"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            
            await update.message.reply_text(
                self.messages[language]["what_bothers"],
                reply_markup=reply_markup
            )
            return CHOOSING_PROBLEM

    async def enter_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle name input."""
        language = context.user_data['language']
        context.user_data['name'] = update.message.text
        
        await update.message.reply_text(
            self.messages[language]["enter_age_class"],
            reply_markup=ReplyKeyboardRemove()
        )
        return ENTER_AGE_CLASS

    async def enter_age_class(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle age and class input."""
        language = context.user_data['language']
        context.user_data['age_class'] = update.message.text
        
        keyboard = []
        for problem in self.messages[language]["problems"]:
            keyboard.append([problem])
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
        
        await update.message.reply_text(
            self.messages[language]["what_bothers"],
            reply_markup=reply_markup
        )
        return CHOOSING_PROBLEM

    async def choose_problem(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        language = context.user_data['language']
        context.user_data['problem'] = update.message.text
        await update.message.reply_text(
            self.messages[language]["describe_situation"],
            reply_markup=ReplyKeyboardRemove()
        )
        return ENTERING_PROBLEM_DETAILS

    async def enter_problem_details(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        language = context.user_data['language']
        context.user_data['problem_details'] = update.message.text
        
        if context.user_data['consultation_mode'] == self.messages[language]["offline"]:
            await update.message.reply_text(
                self.messages[language]["choose_time"]
            )
            return CHOOSING_TIME
        else:
            return await self.finish_conversation(update, context)

    async def choose_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['preferred_time'] = update.message.text
        return await self.finish_conversation(update, context)

    async def finish_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        language = context.user_data['language']
        psychologist = context.user_data['psychologist']
        client_id = update.effective_user.id

        message = (
            f"Новое обращение!\n\n"
            f"Тип консультации: {context.user_data.get('consultation_mode')}\n"
            f"Имя клиента: {context.user_data.get('name', 'Аноним')}\n"
            f"Возраст/класс: {context.user_data.get('age_class', 'Не указано')}\n"
            f"Тип проблемы: {context.user_data.get('problem')}\n"
            f"Детали: {context.user_data.get('problem_details')}\n"
            f"Предпочтительное время: {context.user_data.get('preferred_time', 'Не указано')}\n"
            f"ID клиента: {client_id}"
        )

        keyboard = [
            [
                InlineKeyboardButton("Принять", callback_data=f"accept_{client_id}"),
                InlineKeyboardButton("Отложить", callback_data=f"postpone_{client_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        try:
            await context.bot.send_message(
                chat_id=psychologist['id'],
                text=message,
                reply_markup=reply_markup
            )
            self.active_dialogues[client_id] = {
                'psychologist_id': psychologist['id'],
                'state': 'pending'
            }
            await update.message.reply_text(
                self.messages[language]['thanks'].format(psychologist['name'][language])
            )
        except Exception as e:
            logging.error(f"Failed to send message to psychologist: {e}")
            await update.message.reply_text(
                "Произошла ошибка при отправке сообщения психологу. Пожалуйста, попробуйте снова." if language == "ru" else
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
            
            # Сообщение для психолога (всегда на русском)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text="✅ Диалог начат. Используйте /end для завершения диалога."
            )

            # Определяем язык клиента
            client_language = "ru"
            for dialogue_data in self.active_dialogues.values():
                if dialogue_data.get('psychologist_id') == str(query.message.chat_id):
                    client_language = dialogue_data.get('language', 'ru')
                    break

            # Сообщение для клиента на выбранном языке
            client_messages = {
                "ru": "✅ Психолог принял ваш запрос. Теперь вы можете общаться.",
                "kz": "✅ Психолог сіздің өтінішіңізді қабылдады. Енді сөйлесе аласыз."
            }

            await context.bot.send_message(
                chat_id=client_id,
                text=client_messages[client_language]
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
        
        # Сообщение для психолога (всегда на русском)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="⏳ Запрос отложен. Вы можете вернуться к нему позже."
        )

        # Определяем язык клиента
        client_language = "ru"
        if client_id in self.active_dialogues:
            client_language = self.active_dialogues[client_id].get('language', 'ru')

        # Сообщение для клиента на выбранном языке
        client_messages = {
            "ru": "⏳ Ваш запрос временно отложен. Психолог свяжется с вами позже.",
            "kz": "⏳ Сіздің өтінішіңіз уақытша кейінге қалдырылды. Психолог сізбен кейінірек байланысады."
        }

        await context.bot.send_message(
            chat_id=client_id,
            text=client_messages[client_language]
        )

    async def end_dialogue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /end command - only available for psychologists."""
        user_id = update.effective_user.id
        language = context.user_data.get('language', 'ru')
        
        # Проверяем, является ли пользователь психологом
        is_psychologist = str(user_id) in [p['id'] for p in self.psychologists.values()]
        
        if is_psychologist:
            # Если это психолог, позволяем завершить диалог
            for client_id, dialogue in self.active_dialogues.items():
                if dialogue['psychologist_id'] == str(user_id):
                    await self.close_dialogue(context, client_id, str(user_id), language)
            return ConversationHandler.END
        else:
            # Если это клиент, отправляем сообщение что команда недоступна
            await update.message.reply_text(
                "Диалог может завершить только психолог." if language == "ru" else 
                "Диалогты тек психолог қана аяқтай алады."
            )
            return IN_DIALOGUE

    async def close_dialogue(self, context, client_id, psychologist_id, language):
        if client_id in self.active_dialogues:
            del self.active_dialogues[client_id]
            
            await context.bot.send_message(
                chat_id=client_id,
                text=self.messages[language]["dialog_ended"]
            )
            await context.bot.send_message(
                chat_id=psychologist_id,
                text=f"Диалог с клиентом {client_id} завершен."
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message_text = update.message.text
        language = context.user_data.get('language', 'ru')

        if message_text.startswith('/'):
            return

        is_psychologist = str(user_id) in [p['id'] for p in self.psychologists.values()]

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
                    "У вас нет активных диалогов с клиентами.\n"
                    "Примите запрос клиента, чтобы начать диалог."
                )
        else:
            if user_id in self.active_dialogues and self.active_dialogues[user_id]['state'] == 'active':
                psychologist_id = self.active_dialogues[user_id]['psychologist_id']
                await context.bot.send_message(
                    chat_id=psychologist_id,
                    text=f"Клиент {user_id}: {message_text}"
                )
            else:
                await update.message.reply_text(
                    self.messages[language]["dialog_not_started"]
                )

def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    bot = ClientBot()
    application = Application.builder().token("7237993689:AAGBApQLWmhf1lOXTdERXn0n7VfHRdPd7xk").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', bot.start)],
        states={
            CHOOSING_LANGUAGE: [
                CallbackQueryHandler(bot.choose_language, pattern="^lang_")
            ],
            CHOOSING_PSYCHOLOGIST: [
                CallbackQueryHandler(bot.choose_psychologist, pattern="^psych_")
            ],
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

    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()