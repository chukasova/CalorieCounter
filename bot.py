from apscheduler.jobstores import sqlalchemy

from data_base import add_user, get_user, user_update_weight, user_update_age, user_update_height, user_update_calories, \
    add_new_prod, get_like, add_eaten_product, eat_today, get_user_kkal, get_search_prod, get_last_data
import logging
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CommandHandler,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

HELP = '/start - начало, регистрация пользователя\n' \
       '/mydata - вывести информацию о пользователе\n' \
       '/update - обновить информацию у существующего пользователя\n' \
       '/eat - добавить съеденный продукт за сегодня\n' \
       '/find - проверить продукт в БД\n' \
       '/addprod - добавить новый продукт в БД\n' \
       '/eat_today - вывести список съеденного за сегодня\n' \
       '/last7 - вывести список съеденного за последние 7дней'

TOKEN = "1751878536:AAFLiBmG9i6DSXgkmjT4DszVF2iSMauwPgk"

AGE, GENDER, WEIGHT, HEIGHT = range(4)
SELECTOR1, SELECTOR2 = range(2)
PROD_NAME, PROD_P, PROD_F, PROD_U, PROD_K = range(5)
REQUEST = range(1)
PROD_EAT, PROD_GRAMM = range(2)


def cancel(update: Update, _: CallbackContext):
    update.message.reply_text(
        'Отемана! Введи новую команду.', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def bot_help(update: Update, context: CallbackContext):
    update.message.reply_text(HELP)


def start(update: Update, context: CallbackContext):
    reply_keyboard = [['/start', '/mydata', '/update']]
    res = get_user(update.effective_user.id)
    if res is not None:
        update.message.reply_text(
            'У меня есть необходимые данные о тебе, можно их проверить: /mydata\n'
            'или изменить: /update',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        )
        return ConversationHandler.END
    else:
        update.message.reply_text(
            'Привет! Я бот счетчик калорий. Я могу запоминать что ты ешь и говорить когда остановиться.\n'
            'Чтобы я мог рассчитать данные для тебя мне необходимо задать пару вопросов:\n'
            'Сколько тебе лет?',
        )

    return AGE


def age(update: Update, context: CallbackContext):
    context.user_data['user_age'] = float(update.message.text)
    reply_keyboard = [['Мужской', 'Женский']]
    update.message.reply_text(
        'Выбери свой биологический пол',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return GENDER


def gender(update: Update, context: CallbackContext):
    context.user_data['user_gen'] = update.message.text
    update.message.reply_text(
        'Введи свой текущий вес',
        reply_markup=ReplyKeyboardRemove()
    )

    return WEIGHT


def weight(update: Update, context: CallbackContext):
    context.user_data['user_weight'] = float(update.message.text)
    update.message.reply_text(
        'Введи свой рост',
        reply_markup=ReplyKeyboardRemove()
    )
    return HEIGHT


def bmi(user_height, user_weight):
    bmi_user = user_weight / (user_height / 100) ** 2
    return bmi_user


def calories(user_height, user_weight, user_gen, user_age):
    if user_gen == 'Мужской':
        cal_norm = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) + 5
    else:
        cal_norm = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) + 5
    return cal_norm


def koof_calories(user_height, user_weight, user_gen, user_age):
    bmi_user = bmi(user_height, user_weight)
    cal_norm = calories(user_height, user_weight, user_gen, user_age)
    if bmi_user < 16.5:
        new_col_norm = cal_norm * 1.15
    elif 16.5 <= bmi_user <= 18.4:
        new_col_norm = cal_norm * 1.1
    elif 18.5 <= bmi_user <= 24.9:
        new_col_norm = cal_norm * 1
    elif 25 <= bmi_user <= 30:
        new_col_norm = cal_norm * 0.95
    elif 30.1 <= bmi_user <= 34.9:
        new_col_norm = cal_norm * 0.9
    elif 35 <= bmi_user <= 40:
        new_col_norm = cal_norm * 0.85
    elif bmi_user > 40:
        new_col_norm = cal_norm * 0.8

    else:
        raise Exception
    return new_col_norm


def bmi_printer(update: Update, user_height, user_weight, user_gen, user_age):
    bmi_index = bmi(user_height, user_weight)
    new_col_norm = koof_calories(user_height, user_weight, user_gen, user_age)
    if bmi_index < 16.5:
        update.message.reply_text(
            'Крайний недостаток веса, индекс: {}, рекомендуемая норма: {}'.format(bmi_index, new_col_norm))
    elif 16.5 <= bmi_index <= 18.4:
        update.message.reply_text(
            'Недостаток в весе, индекс: {}, рекомендуемая норма: {}'.format(bmi_index, new_col_norm))
    elif 18.5 <= bmi_index <= 24.9:
        update.message.reply_text(
            'Нормальный вес тела, индекс: {}, рекомендуемая норма: {}'.format(bmi_index, new_col_norm))
    elif 25 <= bmi_index <= 30:
        update.message.reply_text(
            'Избыточная масса тела, индекс: {}, рекомендуемая норма: {}'.format(bmi_index, new_col_norm))
    elif 30.1 <= bmi_index <= 34.9:
        update.message.reply_text(
            'Ожирение (Класс I), индекс: {}, рекомендуемая норма: {}'.format(bmi_index, new_col_norm))
    elif 35 <= bmi_index <= 40:
        update.message.reply_text(
            'Ожирение (Класс II - тяжелое), индекс: {}, рекомендуемая норма: {}'.format(bmi_index, new_col_norm))
    elif bmi_index > 40:
        update.message.reply_text(
            'Ожирение (Класс III - крайне тяжелое), индекс: {}, рекомендуемая норма: {}'.format(bmi_index,
                                                                                                new_col_norm))

    else:
        update.message.reply_text('Ошибка(')

    return new_col_norm


def height(update: Update, context: CallbackContext):
    context.user_data['user_height'] = float(update.message.text)
    update.message.reply_text(
        'Спасибо, теперь у меня есть все необходимые параметры!\n'
        'Можно проверить: /mydata',

    )
    user_height = context.user_data['user_height']
    user_weight = context.user_data['user_weight']
    user_gen = context.user_data['user_gen']
    user_age = context.user_data['user_age']

    context.user_data.clear()
    user_calories = bmi_printer(update, user_height, user_weight, user_gen, user_age)

    add_user(user_id=update.effective_user.id,
             gender=user_gen,
             age=user_age,
             weight=user_weight,
             height=user_height,
             calories=user_calories)

    # print(context.user_data)
    return ConversationHandler.END


def printer_db(update: Update, context: CallbackContext):
    id, gender, weight, height, calories, age = get_user(update.effective_user.id)
    update.message.reply_text(
        'Пол: {};\nВес: {};\nРост: {};\nОптимальная норма ккал/сутки: {};\nВозраст: {}'.format(gender, weight, height,
                                                                                               calories, age)
    )


def update_user_data(update: Update, context: CallbackContext):
    reply_keyboard = [['Возраст', 'Вес', 'Рост']]
    update.message.reply_text(
        'Какой параметр изменить?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return SELECTOR1


def update_user_data_selector(update: Update, context: CallbackContext):
    context.user_data['selected_option'] = selected_option = str(update.message.text)
    if selected_option == 'Вес':
        update.message.reply_text(
            'Введи вес'
        )
    elif selected_option == 'Возраст':
        update.message.reply_text(
            'Введи возраст'
        )
    elif selected_option == 'Рост':
        update.message.reply_text(
            'Введи рост'
        )
    else:
        pass
    return SELECTOR2


def update_user_analys(update: Update, context: CallbackContext):
    selected_option = context.user_data['selected_option']

    if selected_option == 'Вес':
        user_update_weight(update.effective_user.id, weight_new=float(update.message.text))
    elif selected_option == 'Возраст':
        user_update_age(update.effective_user.id, age_new=float(update.message.text))
    elif selected_option == 'Рост':
        user_update_height(update.effective_user.id, height_new=float(update.message.text))
    else:
        pass

    update.message.reply_text(
        'Все обновлено!\n'
        'Хочешь проверить параметры? /mydata \n'
        'Нужно ещё что-то обновить? /update'

    )
    id, gender, weight, height, calories, age = get_user(update.effective_user.id)
    new_col_norm = koof_calories(height, weight, gender, age)
    user_update_calories(update.effective_user.id, calories_new=new_col_norm)
    return ConversationHandler.END


def user_add_prod(update: Update, context: CallbackContext):
    # reply_keyboard = [['/eat', '/eat_today', '/addprod']]
    update.message.reply_text(
        '/addprod помогает добавить новый продукт,\n'
        'введи название продукта:',
        # reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

    )
    return PROD_NAME


def prod_name(update: Update, context: CallbackContext):
    context.user_data['name_product'] = update.message.text
    update.message.reply_text(
        'Введи количество белков на 100гр'
    )
    return PROD_P


def prod_b(update: Update, context: CallbackContext):
    context.user_data['p_product'] = update.message.text
    update.message.reply_text(
        'Введи количество жиров на 100гр'
    )
    return PROD_F


def prod_f(update: Update, context: CallbackContext):
    context.user_data['f_product'] = update.message.text
    update.message.reply_text(
        'Введи количество углеводов на 100гр'
    )
    return PROD_U


def prod_u(update: Update, context: CallbackContext):
    context.user_data['u_product'] = update.message.text
    update.message.reply_text(
        'Введи количество килокалорий на 100гр'
    )
    return PROD_K


def prod_k(update: Update, context: CallbackContext):
    context.user_data['k_product'] = update.message.text

    n_product = context.user_data['name_product']
    p_product = context.user_data['p_product']
    f_product = context.user_data['f_product']
    u_product = context.user_data['u_product']
    k_product = context.user_data['k_product']

    try:
        add_new_prod(
            name_product=n_product,
            fat=f_product,
            prot=p_product,
            ccal=k_product,
            carb=u_product,
        )
        update.message.reply_text(
            'Спаисбо, пробукт добавлен!\n'
            'Добавить продукт в список съеденного сегодня?/eat'
        )
    except Exception:
        update.message.reply_text(
            'Произошла ошибка!\n'
            'Продукт не добавлен!'
        )
    finally:
        context.user_data.clear()

    return ConversationHandler.END


def find_prod(update: Update, context: CallbackContext):
    update.message.reply_text(
        '/find - команда для поиска информации о продукте,\n'
        'введите начальные символы продукта, например "молок"',

    )

    return REQUEST


def request_prod(update: Update, context: CallbackContext):
    res = get_like(update.message.text)

    if res:
        result_str = 'Список совпадений:\n'
        for row in res:
            result_str += '"{1}" {2}\\{3}\\{4} - {5}ккал\n'.format(*row)

        update.message.reply_text(result_str)
    else:
        update.message.reply_text(
            'Нет информации о продукте.'
        )

    return ConversationHandler.END


def eat_start(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Команда /eat запоминает что ты съел сегодня,\n'
        'введи название продукта:',

    )
    return PROD_EAT


def find_product(update: Update, context: CallbackContext):
    name_prod = update.message.text
    result = get_search_prod(name_prod)
    if result:
        context.user_data['id_product'], _, _, _, _, context.user_data['ccal'] = result[0]
        update.message.reply_text(
            'какое кол-во грамм?'
        )
        return PROD_GRAMM
    else:
        res = get_like(name_prod)
        if res:
            result_str = 'Что я нашел:\n'
        else:
            result_str = 'Неизвестный продукт\nможно добавить продукт /addprod\nлибо повторить ввод,\n'

        for row in res:
            result_str += '"{1}" {2}\\{3}\\{4} - {5}ккал\n'.format(*row)
        result_str += 'Введи более точное название продукта или добавь /addprod:'
        update.message.reply_text(result_str)

        return PROD_EAT


def prod_gramm(update: Update, context: CallbackContext):
    gramm_product = float(update.message.text)
    id_product = context.user_data['id_product']
    ccal = context.user_data['ccal']

    add_eaten_product(update.effective_user.id, id_product, gramm_product, ccal * gramm_product / 100)
    update.message.reply_text(
        'Спасибо, все записал!\nДобавить еще?/eat'
    )
    context.user_data.clear()
    return ConversationHandler.END


def eat_today_print(update: Update, context: CallbackContext):
    reply_keyboard = [['/eat', '/eat_today', '/addprod']]
    result = eat_today(update.effective_user.id)
    res_str = 'За сегодня ты съел:\n'
    sum_kkal = 0
    for row in result:
        res_str += '"{}" - {}гр {}ккал\n'.format(*row)
        sum_kkal += row[-1]
    res_str += '\nИтоговая сумма калорий: {}\n'.format(sum_kkal)

    last_kkal = get_user_kkal(update.effective_user.id)[0] - sum_kkal
    res_str += 'На сегодня еще можно съесть {} ккал\n'.format(last_kkal)
    update.message.reply_text(res_str, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


def statistic_last(update: Update, context: CallbackContext):
    # update.message.reply_text(
    #     'команда /last выводит за последние 7дн\n'
    #     )
    # str
    result = get_last_data(update.effective_user.id)
    string = ''
    for row in result:
        string += 'дата: {2}, суммарное кол-ва ккал {1:.0f}\n'.format(*row)
    update.message.reply_text(string)
    return ConversationHandler.END


def run_bot():
    update = Updater(TOKEN, use_context=True)
    dispatcher = update.dispatcher

    dispatcher.add_handler(CommandHandler("eat_today", eat_today_print))
    dispatcher.add_handler(CommandHandler("help", bot_help))
    dispatcher.add_handler(CommandHandler("last7", statistic_last))

    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={

            GENDER: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, gender)],
            WEIGHT: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, weight)],
            HEIGHT: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, height)],
            AGE: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, age)],
        },
        fallbacks=[]
    )

    update_user_handler = ConversationHandler(
        entry_points=[CommandHandler('update', update_user_data)],
        states={
            SELECTOR1: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, update_user_data_selector)],
            SELECTOR2: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, update_user_analys)],
        },
        fallbacks=[]
    )

    user_add_new_product = ConversationHandler(
        entry_points=[CommandHandler('addprod', user_add_prod)],
        states={
            PROD_NAME: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, prod_name)],
            PROD_P: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, prod_b)],
            PROD_F: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, prod_f)],
            PROD_U: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, prod_u)],
            PROD_K: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, prod_k)],

        },
        fallbacks=[]
    )

    find_prod_handler = ConversationHandler(
        entry_points=[CommandHandler('find', find_prod)],
        states={
            REQUEST: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, request_prod)],
        },
        fallbacks=[]
    )

    eat_handler = ConversationHandler(
        entry_points=[CommandHandler('eat', eat_start)],
        states={
            PROD_EAT: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, find_product)],
            PROD_GRAMM: [CommandHandler('cancel', cancel), MessageHandler(Filters.text, prod_gramm)],
        },
        fallbacks=[]
    )

    dispatcher.add_handler(CommandHandler('mydata', printer_db))

    dispatcher.add_handler(registration_handler)
    dispatcher.add_handler(update_user_handler)
    dispatcher.add_handler(user_add_new_product)
    dispatcher.add_handler(find_prod_handler)
    dispatcher.add_handler(eat_handler)
    update.start_polling()
    update.idle()


if __name__ == "__main__":
    run_bot()
