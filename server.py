import os
import youtube_dl as handler_aux
from telegram.ext import Updater, CommandHandler
import re
import pathlib
from subprocess import call
import math
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)





# Define a few command handlers. These usually take the two arguments bot and
# update. Error handlers also receive the raised TelegramError object in error.

''' Start function, very simple and straight forward'''
def start(bot, update):
    update.message.reply_text('Hi! Use /download VideoLink to download a video!'
                              'for more information about the usage, use /download')

'''error handling if needed'''
def error(bot, update, error):
    # logger.warning('Update "%s" caused error "%s"' % (update, error))
    pass


def suggest(bot, update, args):
    chat_id = update.message.chat_id
    try:
        if len(args) > 0:
            suggestion = ''
            for word in args:
                suggestion = suggestion + word + " "
            suggestion = suggestion + "  by  {}".format(chat_id)
            bot.send_message(chat_id=349366414, text=suggestion)
            update.message.reply_text("Thanks for your suggestion!")
        else:
            update.message.reply_text("Hello! If you'd like to suggest a new feature, please use"
                                      "/suggest [and your suggestion Here] :D!")

    except IndexError:
        update.message.reply_text("Hello! If you'd like to suggest a new feature, please use"
                                  "/suggest [and your suggestion Here] :D!")


formatPath = os.path.dirname(os.path.abspath(__file__))


# converting sizes to make it look more readable and less verbose
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1000)))
    p = math.pow(1000, i)
    s = round(size_bytes / p, 2)
    string = "%s %s" % (s, size_name[i])
    return string


# to make numbers readable by inserting commas
# example:  1000 -> 1,000 
def number_readable(number):
    number = str(number)
    orig = number
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', number)
    if orig == new:
        return new
    else:
        return number_readable(new)




opts = {
    # used to output less verbose information
    'no_warnings':True,
    'quiet':True,
    # audios filter
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}

# the main downloading function!
def download(bot, update, args):
    '''special regex used to extract the video id out of any youtube-related link '''
    regex = '((?<=(v|V)/)|(?<=be/)|(?<=(\?|\&)v=)|(?<=embed/))([\w-]+)'
    # chat_id variable for each user of the bot
    chat_id = update.message.chat_id
    try:
        url = str(args[0])
        print(str(chat_id) + ":", str(args[0]))
        video_id = re.search(regex, url)
        # saving into the db the request :>
        if video_id is None:
            update.message.reply_text("Improper link")
        else:
            #regex filtering
            video_id = video_id.group(4)
            # saving the chat id of the user to the chat_id.txt file, 
            # very useful specially when you need to send a message to 
            # all users!
            f = open("chat_id.txt","a+")
            f.write(","+str(chat_id))
            f.close()

            update.message.reply_text("[*] Searching for the video")

        url = "www.youtube.com/watch?v=" + video_id
        try:
            with handler_aux.YoutubeDL(opts) as ydl:
                # video information for the given video
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', None)
                video_duration = info.get("duration", None)
                video_likes = info.get("like_count", None)
                video_dislikes = info.get("dislike_count", None)
                video_size = info.get("filesize", None)
                video_views = info.get("view_count", None)
            video_size_two = video_size
            video_size = video_size / 1024
            video_size = video_size / 1024
            if video_size <= 60:
                # readable_size is for readable size, video size is for another thing
                readable_size = convert_size(video_size_two)
                # video duration is second, so we are converting it to hours,minutes,seconds
                m, s = divmod(video_duration, 60)
                h, m = divmod(m, 60)
                # making the number readable for the eye
                show_title = video_title
                video_views = number_readable(video_views)
                video_dislikes = number_readable(video_dislikes)
                video_likes = number_readable(video_likes)
                video_title = video_title.capitalize().strip().replace(" ", "-").replace("/", "").replace(",", "").replace("\\","").replace(")","").replace("(","").replace("*","").replace("[","").replace("]","")
                video_title = video_title.replace("---","-").replace("--","-")
                video_title = video_title[:40]
                # checking if hour does exist, so we put it in the string
                # otherwise: we just plug in minutes, seconds
                if h > 0:
                    fullTime = '{}:{}:{}'.format(h, m, s)
                else:
                    fullTime = '{}:{}'.format(m, s)
                    # checking if video size exceeds the normal limit [50 MB]

                update.message.reply_text(
                    "[" + show_title + "]\n" +
                    "[👁]->" + str(video_views) + "\n"
                    + "[👍]-> " + str(video_likes) + "    [👎]-> \t   " + str(video_dislikes) + "\n"
                    + "[🕠]-> " + fullTime + "    [💾]->\t   " + str(readable_size) + " [Before converting]"
                )
                path = pathlib.Path('audios/' + video_title + '.mp3')
                ydl_opts = {
                    'outtmpl': formatPath + '/audios/' + video_title + '.%(ext)s',
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                }
                filepath = formatPath + '/audios/' + video_title + '.mp3'
                with handler_aux.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([str(url)])
                final_size = os.path.getsize(filepath)
                final_size = final_size / 1024
                final_size = final_size / 1024
                show_size = os.path.getsize(filepath)
                if final_size <= 50:
                    update.message.reply_text("Processing file \n"
                                              + "[After converting: {}]".format(
                        str(final_size)[:4] + "MB"
                    ))
                    audio = open(filepath, 'rb')
                    bot.send_audio(chat_id=chat_id, audio=audio, timeout=120)
                else:
                    update.message.reply_text(
                        "[" + show_title + "] \n" +
                        "[👁]->" + str(video_views) + "\n"
                        + "[👍]-> " + str(video_likes) + "    [👎]-> \t   " + str(video_dislikes) + "\n"
                        + "[🕠]-> " + fullTime + "   [💾]->\t   " + str(readable_size) + "MB \n" +
                        "Video size exceeds maximum telegram limits ")
            else:
                # readable_size is for readable size, video size is for another thing
                readable_size = convert_size(video_size_two)
                # video duration is second, so we are converting it to hours,minutes,seconds
                m, s = divmod(video_duration, 60)
                h, m = divmod(m, 60)
                # making the number readable for the eye
                video_views = number_readable(video_views)
                video_dislikes = number_readable(video_dislikes)
                video_likes = number_readable(video_likes)
                # checking if hour does exist, so we put it in the string
                # otherwise: we just plug in minutes, seconds
                if h > 0:
                    fullTime = '{}:{}:{}'.format(h, m, s)
                else:
                    fullTime = '{}:{}'.format(m, s)
                    # checking if video size exceeds the normal limit [50 MB]
                update.message.reply_text(
                    "[" + video_title + "] \n" +
                    "[👁]->" + str(video_views) + "\n"
                    + "[👍]-> " + str(video_likes) + "    [👎]-> \t   " + str(video_dislikes) + "\n"
                    + "[🕠]-> " + fullTime + "   [💾]->\t   " + str(readable_size) + " \n" +
                    "Video size exceeds maximum telegram limits ")

        except:
            # Used when the link isn't proper enough
            update.message.reply_text("improper link")
        finally:
            # this little part deletes the video after downloading
            # comment whatever below if you don't want this feature
            # specially used for those who don't have a big storage 
            filepath = formatPath + "/audios/"
            call("rm -rf " + filepath + "/*", shell=True)

    except (IndexError, ValueError):
        # except when user inputs something like /download
        # so it throws IndexError and is handled here
        update.message.reply_text('Hi! Use /download VideoLink to download a video'
                                  'You could also type /download YoutubeURL ArtistName [the artist name is optional]')




# about function 
def about(bot, update):
    update.message.reply_text('YoutubeMp3Downloader - made by @C00kiie \n'+
                              'For more information & updates visit this channel: https://t.me/cookieapi')

'''Token below'''
token = '438565192:AAHAQah0LfbzMPdFWhfLCPSzbQ0KwGez15E'
updater = Updater(token)
# Get the dispatcher to register handlers
dp = updater.dispatcher
# on different commands - answer in Telegram
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("about", about))
dp.add_handler(CommandHandler("download", download, pass_args=True))
dp.add_handler(CommandHandler("suggest", suggest, pass_args=True))

# dp.add_error_handler(error)

# Start the Bot
updater.start_polling()

# Block until you press Ctrl-C or the process receives SIGINT, SIGTERM or
# SIGABRT. This should be used  most of the time, since start_polling() is
# non-blocking and will stop the bot gracefully.
updater.idle()
