# машинное обучения для реализации возможности угадывания намерений
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

from vosk import Model, KaldiRecognizer  # оффлайн-распознавание от Vosk
from googlesearch import search  # поиск в Google
from pyowm import OWM  # использование OpenWeatherMap для получения данных о погоде
from termcolor import colored  # вывод цветных логов (для выделения распознанной речи)
from dotenv import load_dotenv  # загрузка информации из .env-файла
import speech_recognition  # распознавание пользовательской речи (Speech-To-Text)
import googletrans  # использование системы Google Translate
import pyttsx3  # синтез речи (Text-To-Speech)
import wikipediaapi  # поиск определений в Wikipedia
import random  # генератор случайных чисел
import webbrowser  # работа с использованием браузера по умолчанию (открывание вкладок с web-страницей)
import traceback  # вывод traceback без остановки работы программы при отлове исключений
import json  # работа с json-файлами и json-строками
import wave  # создание и чтение аудиофайлов формата wav
import os  # работа с файловой системой
import datetime  # требуется для разрешения любого запроса относительно даты и времени
import time

start_time: float = 0

class Translation:
    """
    Получение вшитого в приложение перевода строк для создания мультиязычного ассистента
    """
    with open("translations.json", "r", encoding="UTF-8") as file:
        translations = json.load(file)

    def get(self, text: str):
        """
        Получение перевода строки из файла на нужный язык (по его коду)
        :param text: текст, который требуется перевести
        :return: вшитый в приложение перевод текста
        """
        if text in self.translations:
            return self.translations[text][assistant.speech_language]
        else:
            # в случае отсутствия перевода происходит вывод сообщения об этом в логах и возврат исходного текста
            print(colored("Not translated phrase: {}".format(text), "red"))
            return text


class OwnerPerson:
    """
    Информация о владельце, включающие имя, город проживания, родной язык речи, изучаемый язык (для переводов текста)
    """
    name = ""
    home_city = ""
    native_language = ""
    target_language = ""


class VoiceAssistant:
    """
    Настройки голосового ассистента, включающие имя, пол, язык речи
    Примечание: для мультиязычных голосовых ассистентов лучше создать отдельный класс,
    который будет брать перевод из JSON-файла с нужным языком
    """
    name = ""
    sex = ""
    speech_language = ""
    recognition_language = ""


def setup_assistant_voice():
    """
    Установка голоса по умолчанию (индекс может меняться в зависимости от настроек операционной системы)
    """
    voices = ttsEngine.getProperty("voices")

    if assistant.speech_language == "en":
        assistant.recognition_language = "en-US"
        if assistant.sex == "female":
            # Microsoft Zira Desktop - English (United States)
            ttsEngine.setProperty("voice", voices[1].id)
        else:
            # Microsoft David Desktop - English (United States)
            ttsEngine.setProperty("voice", voices[2].id)
    else:
        assistant.recognition_language = "ru-RU"
        # Microsoft Irina Desktop - Russian
        ttsEngine.setProperty("voice", voices[0].id)


def record_and_recognize_audio(*args: tuple):
    """
    Запись и распознавание аудио
    """
    with microphone:
        recognized_data = ""

        # запоминание шумов окружения для последующей очистки звука от них
        recognizer.adjust_for_ambient_noise(microphone, duration=2)

        try:
            print("Listening...")
            audio = recognizer.listen(microphone, 5, 5)

            with open("microphone-results.wav", "wb") as file:
                file.write(audio.get_wav_data())

        except speech_recognition.WaitTimeoutError:
            play_voice_assistant_speech(translator.get("Can you check if your microphone is on, please?"))
            traceback.print_exc()
            return

        # использование online-распознавания через Google (высокое качество распознавания)
        try:
            print("Started recognition...")
            recognized_data = recognizer.recognize_google(audio, language=assistant.recognition_language).lower()

        except speech_recognition.UnknownValueError:
            pass  # play_voice_assistant_speech("What did you say again?")

        # в случае проблем с доступом в Интернет происходит попытка использовать offline-распознавание через Vosk
        except speech_recognition.RequestError:
            print(colored("Trying to use offline recognition...", "cyan"))
            recognized_data = use_offline_recognition()

        return recognized_data


def use_offline_recognition():
    """
    Переключение на оффлайн-распознавание речи
    :return: распознанная фраза
    """
    recognized_data = ""
    try:
        # проверка наличия модели на нужном языке в каталоге приложения
        if not os.path.exists("models/vosk-model-small-" + assistant.speech_language + "-0.4"):
            print(colored("Please download the model from:\n"
                          "https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.",
                          "red"))
            exit(1)

        # анализ записанного в микрофон аудио (чтобы избежать повторов фразы)
        wave_audio_file = wave.open("microphone-results.wav", "rb")
        model = Model("models/vosk-model-small-" + assistant.speech_language + "-0.4")
        offline_recognizer = KaldiRecognizer(model, wave_audio_file.getframerate())

        data = wave_audio_file.readframes(wave_audio_file.getnframes())
        if len(data) > 0:
            if offline_recognizer.AcceptWaveform(data):
                recognized_data = offline_recognizer.Result()

                # получение данных распознанного текста из JSON-строки (чтобы можно было выдать по ней ответ)
                recognized_data = json.loads(recognized_data)
                recognized_data = recognized_data["text"]
    except:
        traceback.print_exc()
        print(colored("Sorry, speech service is unavailable. Try again later", "red"))

    return recognized_data


def play_voice_assistant_speech(text_to_speech):
    """
    Проигрывание речи ответов голосового ассистента (без сохранения аудио)
    :param text_to_speech: текст, который нужно преобразовать в речь
    """
    ttsEngine.say(str(text_to_speech))
    ttsEngine.runAndWait()


def play_failure_phrase(*args: tuple):
    """
    Проигрывание случайной фразы при неудачном распознавании
    """
    failure_phrases = [
        translator.get("Can you repeat, please?"),
        translator.get("What did you say again?"),
        translator.get("Repeat, please"),
        translator.get("I don't understand you")
    ]
    play_voice_assistant_speech(failure_phrases[random.randint(0, len(failure_phrases) - 1)])


def play_greetings(*args: tuple):
    """
    Проигрывание случайной приветственной речи
    """
    greetings = [
        translator.get("Hello, {}! How can I help you today?").format(person.name),
        translator.get("Good day to you {}! How can I help you today?").format(person.name),
        translator.get("Hello, {}! What are we going to do today?").format(person.name),
        translator.get("{} welcomes you!").format(assistant.name),
        translator.get("Hello, {}! I am {}. Your voice assistant. How can I help you?").format(person.name,assistant.name),
        translator.get("Hello, {}! Did you want something?").format(person.name)
    ]
    play_voice_assistant_speech(greetings[random.randint(0, len(greetings) - 1)])


def play_farewell_and_quit(*args: tuple):
    """
    Проигрывание прощательной речи и выход
    """
    farewells = [
        translator.get("Goodbye, {}! Have a nice day!").format(person.name),
        translator.get("See you soon, {}!").format(person.name),
        translator.get("Bye-bye!"),
        translator.get("I hope I was able to help you, goodbye!"),
        translator.get("See you, {}. Have a nice day!").format(person.name),
        translator.get("{} says goodbye to you!").format(assistant.name)
    ]
    play_voice_assistant_speech(farewells[random.randint(0, len(farewells) - 1)])
    ttsEngine.stop()
    quit()


def tell_about_skills(*args: tuple):

    print(translator.get("• weather forecast ('weather forecast'/'weather')"))
    print(translator.get("• search on Google, YouTube or Wikipedia ('google'/'find video'/'find definition')"))
    print(translator.get("• run person through social nets databases ('find person')"))
    print(translator.get("• translation into another language ('translate'/'find translation')"))
    print(translator.get("• toss coin ('toss/flip coin')"))
    print(translator.get("• current time ('what time'/'current time')"))
    print(translator.get("• calculator ('count'/'calculate')"))
    print(translator.get("• stopwatch ('stopwatch start'/'stopwatch stop')"))
    print(translator.get("• jokes ('joke'/'anecdote')"))
    play_voice_assistant_speech(translator.get("I can tell you about the weather in your city; "
                                               "search for any of your queries in Google, YouTube or Wikipedia; "
                                               "find a person on social networks; "
                                               "help with the translation of a word or phrase into another language; "
                                               "flip a coin to make a difficult decision; tell the time; "
                                               "be a simple calculator; mark the time, and even cheer up, telling hilarious jokes."))


def search_for_term_on_google(*args: tuple):
    """
    Поиск в Google с автоматическим открытием ссылок (на список результатов и на сами результаты, если возможно)
    :param args: фраза поискового запроса
    """
    if not args[0]: return
    search_term = " ".join(args[0])

    # открытие ссылки на поисковик в браузере
    url = "https://google.com/search?q=" + search_term
    webbrowser.get().open(url)

    # альтернативный поиск с автоматическим открытием ссылок на результаты (в некоторых случаях может быть небезопасно)
    search_results = []
    try:
        for _ in search(search_term,  # что искать
                        tld="com",  # верхнеуровневый домен
                        lang=assistant.speech_language,  # используется язык, на котором говорит ассистент
                        num=1,  # количество результатов на странице
                        start=0,  # индекс первого извлекаемого результата
                        stop=1,  # индекс последнего извлекаемого результата (я хочу, чтобы открывался первый результат)
                        pause=1.0,  # задержка между HTTP-запросами
                        ):
            search_results.append(_)
            webbrowser.get().open(_)

    # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
    except:
        play_voice_assistant_speech(translator.get("Seems like we have a trouble. See logs for more information"))
        traceback.print_exc()
        return

    print(search_results)
    play_voice_assistant_speech(translator.get("Here is what I found for {} on google").format(search_term))


def search_for_video_on_youtube(*args: tuple):
    """
    Поиск видео на YouTube с автоматическим открытием ссылки на список результатов
    :param args: фраза поискового запроса
    """
    if not args[0]: return
    search_term = " ".join(args[0])
    url = "https://www.youtube.com/results?search_query=" + search_term
    webbrowser.get().open(url)
    play_voice_assistant_speech(translator.get("Here is what I found for {} on youtube").format(search_term))


def search_for_definition_on_wikipedia(*args: tuple):
    """
    Поиск в Wikipedia определения с последующим озвучиванием результатов и открытием ссылок
    :param args: фраза поискового запроса
    """
    if not args[0]: return

    search_term = " ".join(args[0])

    # установка языка (в данном случае используется язык, на котором говорит ассистент)
    wiki = wikipediaapi.Wikipedia(assistant.speech_language)

    # поиск страницы по запросу, чтение summary, открытие ссылки на страницу для получения подробной информации
    wiki_page = wiki.page(search_term)
    try:
        if wiki_page.exists():
            play_voice_assistant_speech(translator.get("Here is what I found for {} on Wikipedia").format(search_term))
            webbrowser.get().open(wiki_page.fullurl)

            # чтение ассистентом первых двух предложений summary со страницы Wikipedia
            # (могут быть проблемы с мультиязычностью)
            play_voice_assistant_speech(wiki_page.summary.split(".")[:2])
        else:
            # открытие ссылки на поисковик в браузере в случае, если на Wikipedia не удалось найти ничего по запросу
            play_voice_assistant_speech(translator.get(
                "Can't find {} on Wikipedia. But here is what I found on google").format(search_term))
            url = "https://google.com/search?q=" + search_term
            webbrowser.get().open(url)

    # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
    except:
        play_voice_assistant_speech(translator.get("Seems like we have a trouble. See logs for more information"))
        traceback.print_exc()
        return


def get_translation(*args: tuple):
    """
    Получение перевода текста с одного языка на другой (в данном случае с изучаемого на родной язык или обратно)
    :param args: фраза, которую требуется перевести
    """
    if not args[0]: return

    search_term = " ".join(args[0])
    google_translator = googletrans.Translator(service_urls=['translate.googleapis.com'])
    translation_result = ""

    old_assistant_language = assistant.speech_language
    try:
        # если язык речи ассистента и родной язык пользователя различаются, то перевод выполяется на родной язык
        if assistant.speech_language != person.native_language:
            translation_result = google_translator.translate(search_term,  # что перевести
                                                             src=person.target_language,  # с какого языка
                                                             dest=person.native_language)  # на какой язык

            play_voice_assistant_speech("The translation for {} in Russian is".format(search_term))

            # смена голоса ассистента на родной язык пользователя (чтобы можно было произнести перевод)
            assistant.speech_language = person.native_language
            setup_assistant_voice()

        # если язык речи ассистента и родной язык пользователя одинаковы, то перевод выполяется на изучаемый язык
        else:
            translation_result = google_translator.translate(search_term,  # что перевести
                                                             src=person.native_language,  # с какого языка
                                                             dest=person.target_language)  # на какой язык
            play_voice_assistant_speech("По-английски {} будет как".format(search_term))

            # смена голоса ассистента на изучаемый язык пользователя (чтобы можно было произнести перевод)
            assistant.speech_language = person.target_language
            setup_assistant_voice()

        # произнесение перевода
        play_voice_assistant_speech(translation_result.text)

    # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
    except:
        play_voice_assistant_speech(translator.get("Seems like we have a trouble. See logs for more information"))
        traceback.print_exc()

    finally:
        # возвращение преждних настроек голоса помощника
        assistant.speech_language = old_assistant_language
        setup_assistant_voice()


def get_weather_forecast(*args: tuple):
    """
    Получение и озвучивание прогноза погоды
    :param args: город, по которому должен выполняться запос
    """
    # в случае наличия дополнительного аргумента - запрос погоды происходит по нему,
    # иначе - используется город, заданный в настройках
    city_name = person.home_city

    if args:
        if args[0]:
            city_name = args[0][0]

    try:
        # использование API-ключа, помещённого в .env-файл по примеру WEATHER_API_KEY = "01234abcd....."
        # weather_api_key = os.getenv("WEATHER_API_KEY")

        # использование API-ключа
        open_weather_map = OWM('8a10b8453cd18d969802724bdc3d047b')

        # запрос данных о текущем состоянии погоды
        weather_manager = open_weather_map.weather_manager()
        observation = weather_manager.weather_at_place(city_name)
        weather = observation.weather

    # поскольку все ошибки предсказать сложно, то будет произведен отлов с последующим выводом без остановки программы
    except:
        play_voice_assistant_speech(translator.get("Seems like we have a trouble. See logs for more information"))
        traceback.print_exc()
        return

    # разбивание данных на части для удобства работы с ними
    status = weather.detailed_status
    temperature = weather.temperature('celsius')["temp"]
    wind_speed = weather.wind()["speed"]
    pressure = int(weather.pressure["press"] / 1.333)  # переведено из гПА в мм рт.ст.

    # вывод логов
    print(colored("Weather in " + city_name +
                  ":\n * Status: " + status +
                  "\n * Wind speed (m/sec): " + str(wind_speed) +
                  "\n * Temperature (Celsius): " + str(temperature) +
                  "\n * Pressure (mm Hg): " + str(pressure), "yellow"))

    # озвучивание текущего состояния погоды ассистентом (здесь для мультиязычности требуется дополнительная работа)
    play_voice_assistant_speech(translator.get("It is {0} in {1}").format(status, city_name))
    play_voice_assistant_speech(translator.get("The temperature is {} degrees Celsius").format(str(temperature)))
    play_voice_assistant_speech(translator.get("The wind speed is {} meters per second").format(str(wind_speed)))
    play_voice_assistant_speech(translator.get("The pressure is {} mm Hg").format(str(pressure)))


def change_language(*args: tuple):
    """
    Изменение языка голосового ассистента (языка распознавания речи)
    """
    assistant.speech_language = "ru" if assistant.speech_language == "en" else "en"
    setup_assistant_voice()
    print(colored("Language switched to " + assistant.speech_language, "cyan"))


def run_person_through_social_nets_databases(*args: tuple):
    """
    Поиск человека по базе данных социальной сети ВКонтакте
    :param args: имя, фамилия
    """
    if not args[0]: return

    google_search_term = " ".join(args[0])
    vk_search_term = "_".join(args[0])
    fb_search_term = "-".join(args[0])

    # открытие ссылки на поисковик в браузере
    url = "https://google.com/search?q=" + google_search_term + " site: vk.com"
    webbrowser.get().open(url)

    # открытие ссылки на поисковик социальной сети в браузере
    vk_url = "https://vk.com/people/" + vk_search_term
    webbrowser.get().open(vk_url)

    play_voice_assistant_speech(translator.get("Here is what I found for {} on social nets").format(google_search_term))


def toss_coin(*args: tuple):
    """
    "Подбрасывание" монетки для выбора из 2 опций
    """
    flips_count, heads, tails = 3, 0, 0

    for flip in range(flips_count):
        if random.randint(0, 1) == 0:
            heads += 1

    tails = flips_count - heads
    winner = "Tails" if tails > heads else "Heads"
    play_voice_assistant_speech(translator.get(winner) + " " + translator.get("won"))


def get_time(*args: tuple):

    strtime = datetime.datetime.now().strftime('%H:%M:%S')

    nowtime = [
        translator.get("The time is {}").format(strtime),
        translator.get("Current time is {}").format(strtime),
        translator.get("It is {} on the clock").format(strtime)
    ]
    play_voice_assistant_speech(nowtime[random.randint(0, len(nowtime) - 1)])


def tell_mood(*args: tuple):

    moods = [
        translator.get("I'm doing great, thank you for asking"),
        translator.get("So far, it's fine..."),
        translator.get("Will it affect your request in any way?"),
        translator.get("Everything is all right!"),
        translator.get("Everything is fine, but if you paid me for my work, it would be even better"),
        translator.get("There's a lot to do... Let's get started"),
        translator.get("Everything was fine, but I heard you and it got even better!"),
        translator.get("Give me a case and we'll find out"),
        translator.get("Great mood on such a beautiful day!")
    ]
    play_voice_assistant_speech(moods[random.randint(0, len(moods) - 1)])


def calculate(*args: tuple):

    ans: float = 0
    try:
        list_of_nums = args[0]  # '2 + 2'
        num_1, num_2 = int((list_of_nums[-3]).strip()), int((list_of_nums[-1]).strip())
        opers = [list_of_nums[0].strip(), list_of_nums[-2].strip()]
        for i in opers:
            if 'дел' in i or 'множ' in i or 'лож' in i or 'приба' in i or 'выч' in i or i == 'x' or i == 'х' or i == '+' or i == '/' or i == '-' or i == '*':
                oper = i
                break
            else:
                oper = opers[1]
        if oper == "+" or 'слож' in oper:
            ans = num_1 + num_2
        elif oper == "-" or 'выче' in oper:
            ans = num_1 - num_2
        elif oper == "х" or oper == 'x' or 'множ' in oper or oper == '*':
            ans = num_1 * num_2
        elif oper == "/" or 'дел' in oper:
            if num_2 != 0:
                ans = num_1 / num_2
            else:
                play_voice_assistant_speech(translator.get("Division by zero!"))
        elif "степен" in oper:
            ans = num_1 ** num_2
        play_voice_assistant_speech("{0} {1} {2} = {3}".format(list_of_nums[-3], list_of_nums[-2], list_of_nums[-1], round(ans,2)))
    except:
        play_voice_assistant_speech(translator.get("Say, for example: Count 5+5"))


def tell_joke(*args: tuple):

    jokes = [
        translator.get("Make a two-digit number from 10 to 19. Subtract 9. Add 11. Close your eyes. It's dark, isn't it?"),
        translator.get("'I'm going to bed early today' from the creators of 'Tomorrow I will start going to the gym'."),
        translator.get("The programmer decided to borrow 1000 rubles from a friend, but to make it equal, he took 1024."),
        translator.get("Scientists have found that nothing is clear to the hedgehog."),
        translator.get("I was asked to make a contribution for a new pool. I had to give them a glass of water."),
        translator.get("The hourglass struck midnight"),
        translator.get("First snake: I hope I’m not poisonous. Second snake: Why? First snake: Because I bit my lip!"),
        translator.get("Don't be angry with the lazy ones. They didn't do anything."),
        translator.get("How to make light with water? Wash the windows"),
        translator.get("The brown bear asks the white one: Tell me, what kind of soap do you use?"),
        translator.get("Which hand is better to stir the tea with? It is better to stir the tea with a spoon."),
        translator.get("Scientists have found that cats adhere to the principle of 'eating tired sleeping'. During the day, they just put a comma in different places."),
        translator.get("- What is your dog's name? - I don't know, she won't admit it")
    ]
    play_voice_assistant_speech(jokes[random.randint(0, len(jokes) - 1)])


def start_stopwatch(*args: tuple):

    global start_time

    if "запус" in str(args[0]) or "старт" in str(args[0])or "start" in str(args[0]):
        start_time = time.time()
        play_voice_assistant_speech(translator.get("The stopwatch is running"))

    elif "остан" in str(args[0]) or "стоп" in str(args[0])or "stop" in str(args[0]):
        if start_time != 0:
            ttime = time.time() - start_time

            print("Прошло {0} часов {1} минут {2} секунд".format(round(ttime // 3600), round(ttime // 60), round(ttime % 60, 2)))
            play_voice_assistant_speech("Прошло {0} часов {1} минут {2} секунд".format(round(ttime // 3600), round(ttime // 60), round(ttime % 60, 2)))

            start_time = 0
        else:
            play_voice_assistant_speech(translator.get("The stopwatch is off"))


# перечень команд для использования в виде JSON-объекта
config = {
    "intents": {
        "greeting": {
            "examples": ["привет", "здравствуй", "доброе утро", "добрый день",
                         "hi", "hello", "good morning", "good afternoon"],
            "responses": play_greetings
        },
        "farewell": {
            "examples": ["пока", "увидимся", "спокойной ночи", "до встречи",
                         "goodbye", "bye", "see you soon", "night"],
            "responses": play_farewell_and_quit
        },
        "google_search": {
            "examples": ["найди в гугле", "загугли", "поищи в гугле", "гугл",
                         "search on google", "google", "find on google"],
            "responses": search_for_term_on_google
        },
        "youtube_search": {
            "examples": ["найди видео", "покажи видео", "включи видео", "видео",
                         "find video", "find on youtube", "search on youtube", "video"],
            "responses": search_for_video_on_youtube
        },
        "wikipedia_search": {
            "examples": ["найди определение", "найди на википедии", "что такое", "поведай о",
                         "find on wikipedia", "find definition", "narrate about", "what is"],
            "responses": search_for_definition_on_wikipedia
        },
        "person_search": {
            "examples": ["пробей имя", "найди человека", "поищи человека",
                         "find person", "run person", "search for person"],
            "responses": run_person_through_social_nets_databases
        },
        "weather_forecast": {
            "examples": ["прогноз погоды", "погода", "температура", "прогноз",
                         "weather forecast", "report weather", "forecast", "weather"],
            "responses": get_weather_forecast
        },
        "translation": {
            "examples": ["выполни перевод", "переведи", "скажи по-другому", "перевод",
                         "translate", "find translation", "in a different way", "translation"],
            "responses": get_translation
        },
        "language": {
            "examples": ["смени язык", "поменяй язык", "давай теперь", "переключись",
                         "change speech language", "language", "switch", "change"],
            "responses": change_language
        },
        "toss_coin": {
            "examples": ["подбрось монетку", "подкинь монетку", "монетк", "кинь монетку",
                         "toss coin", "coin", "flip a coin", "flip"],
            "responses": toss_coin
        },
        "time": {
            "examples": ["который час", "сколько времени", "посмотри на часы", "текущее время",
                         "time", "look at the clock", "show me the time", "current time"],
            "responses": get_time
        },
        "mood": {
            "examples": ["как дела", "дела", "как настроение", "настроение",
                         "how are you", "how is your mood", "what's up", "how you doing"],
            "responses": tell_mood
        },
        "calculator": {
            "examples": ["посчитай", "вычисли", "кулькулятор", "рассчитай",
                         "count", "calculate", "how much are", "compute"],
            "responses": calculate
        },
        "joke": {
            "examples": ["пошути", "расскажи шутку", "расскажи анекдот", "анекдот",
                         "joke", "tell a joke", "I'm sad", "anecdote"],
            "responses": tell_joke
        },
        "stopwatch": {
            "examples": ["секундомер", "таймер", "отсчет времени", "отсчет",
                         "stopwatch", "mark the time", "timer", "countdown"],
            "responses": start_stopwatch
        },
        "skills": {
            "examples": [" что умеешь", "умеешь", "что можешь", "можешь",
                         "skills", "о себе", "what you can", "help"],
            "responses": tell_about_skills
        }
    },

    "failure_phrases": play_failure_phrase
}


def prepare_corpus():
    """
    Подготовка модели для угадывания намерения пользователя
    """
    corpus = []
    target_vector = []
    for intent_name, intent_data in config["intents"].items():
        for example in intent_data["examples"]:
            corpus.append(example)
            target_vector.append(intent_name)

    training_vector = vectorizer.fit_transform(corpus)
    classifier_probability.fit(training_vector, target_vector)
    classifier.fit(training_vector, target_vector)


def get_intent(request):
    """
    Получение наиболее вероятного намерения в зависимости от запроса пользователя
    :param request: запрос пользователя
    :return: наиболее вероятное намерение
    """
    best_intent = classifier.predict(vectorizer.transform([request]))[0]

    index_of_best_intent = list(classifier_probability.classes_).index(best_intent)
    probabilities = classifier_probability.predict_proba(vectorizer.transform([request]))[0]

    best_intent_probability = probabilities[index_of_best_intent]

    # при добавлении новых намерений стоит уменьшать этот показатель
    print(best_intent_probability)
    if best_intent_probability > 0.1:
        return best_intent


def make_preparations():
    """
    Подготовка глобальных переменных к запуску приложения
    """
    global recognizer, microphone, ttsEngine, person, assistant, translator, vectorizer, classifier_probability, classifier

    # инициализация инструментов распознавания и ввода речи
    recognizer = speech_recognition.Recognizer()
    microphone = speech_recognition.Microphone()

    # инициализация инструмента синтеза речи
    ttsEngine = pyttsx3.init()

    # настройка данных пользователя
    person = OwnerPerson()
    person.name = "Dasha"
    person.home_city = "Novosibirsk"
    person.native_language = "ru"
    person.target_language = "en"

    # настройка данных голосового помощника
    assistant = VoiceAssistant()
    assistant.name = "Zina"
    assistant.sex = "female"
    assistant.speech_language = "ru"

    # установка голоса по умолчанию
    setup_assistant_voice()

    # добавление возможностей перевода фраз (из заготовленного файла)
    translator = Translation()

    # загрузка информации из .env-файла (там лежит API-ключ для OpenWeatherMap)
    load_dotenv()

    # подготовка корпуса для распознавания запросов пользователя с некоторой вероятностью (поиск похожих)
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 3))
    classifier_probability = LogisticRegression()
    classifier = LinearSVC()
    prepare_corpus()


if __name__ == "__main__":
    make_preparations()

    while True:
        # старт записи речи с последующим выводом распознанной речи и удалением записанного в микрофон аудио
        voice_input = record_and_recognize_audio()

        if os.path.exists("microphone-results.wav"):
            os.remove("microphone-results.wav")

        print(colored(voice_input, "blue"))

        # отделение комманд от дополнительной информации (аргументов)
        if voice_input:
            voice_input_parts = voice_input.split(" ")

            # если было сказано одно слово - выполняем команду сразу без дополнительных аргументов
            if len(voice_input_parts) == 1:
                intent = get_intent(voice_input)
                if intent:
                    config["intents"][intent]["responses"]()
                else:
                    config["failure_phrases"]()

            # в случае длинной фразы - выполняется поиск ключевой фразы и аргументов через каждое слово,
            # пока не будет найдено совпадение
            if len(voice_input_parts) > 1:
                for guess in range(len(voice_input_parts)):
                    intent = get_intent((" ".join(voice_input_parts[0:guess])).strip())
                    print(intent)
                    if intent:
                        command_options = [voice_input_parts[guess:len(voice_input_parts)]]
                        print(command_options)
                        config["intents"][intent]["responses"](*command_options)
                        break
                    if not intent and guess == len(voice_input_parts)-1:
                        config["failure_phrases"]()
