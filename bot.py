import os
import telebot
import praw
from prawcore import ResponseException
import html
from time import sleep
import time
import datetime
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
bot = telebot.TeleBot(API_KEY)
reddit = praw.Reddit(client_id=os.environ.get("CLIENT_ID"),
                      client_secret=os.environ.get("CLIENT_SECRET"),
                      username=os.environ.get("USERNAME"),
                      password= os.environ.get("PASSWORD"),
                      user_agent="useragent")

reddit.read_only = True
chatID = None
sex = None
watchList = []
forum = None
flag = True


def extract_arg(arg):
  return arg.split(' ', 1)[1]

def listToNumberedList():
  global watchList
  copy = watchList[:]
  for i in range(len(watchList)):
    copy[i] = str(i+1) + ". " + copy[i].title()
  text = '\n'.join(copy)
  return text;

def submissionsWithinAWeek(forum):
    subreddit = reddit.subreddit(forum)
    submissionsLastWeek = []
    for submission in subreddit.new(limit=100): 
        utcPostTime = submission.created
        submissionDate = datetime.utcfromtimestamp(utcPostTime)

        currentTime = datetime.utcnow()

        #How long ago it was posted.
        submissionDelta = currentTime - submissionDate
        submissionDelta = str(submissionDelta)
        if 'week' not in submissionDelta:
            submissionsLastWeek.append(submission)
    
    return submissionsLastWeek

@bot.message_handler(commands=["start"])
def greeting(message):
  global chatID 
  chatID = message.chat.id
  bot.reply_to(message, "Hey, how's it going? I'm your frugal fashionista! To get me working properly, use /male or /female to set the types of " + 
          "fashion deals you want to look out for. Then, use /addbrand your-brand-here to add your favourite brands to your watch list. " + 
          " Finally, use /hmu to get me started :D")

@bot.message_handler(commands=["gender"])
def viewGender(message):
  global sex
  if (sex):
    bot.reply_to(message, f"Current gender set to {sex}")
  else:
    bot.reply_to(message, "You have not set your gender yet. Use /male or /female to set it.")

@bot.message_handler(commands=["male"])
def male(message):
  #sets the sex to male, which then subscribes the user to deals appearing in frugalmalefashion
  global sex 
  sex = "male"
  global forum 
  forum = "frugalmalefashion"
  bot.reply_to(message, "You are now paying attention to Male fashion deals")

@bot.message_handler(commands=["female"])
def female(message):
  #sets the sex to female, which then subscribes the user to deals appearing in FrugalFemaleFashion
  global sex 
  sex = "female"
  global forum 
  forum = "FrugalFemaleFashion"
  bot.reply_to(message, "You are now paying attention to Female fashion deals")

@bot.message_handler(commands=["addbrand"])
def addBrand(message):
  #users should add popular acronyms of the brands that they want to look out for; commes des garcons and CDG.
  global watchList
  try:
    name = extract_arg(message.text)
    if name not in watchList:
      watchList.append(name.lower())
      answer = listToNumberedList()
      bot.reply_to(message, f"{name.title()} has been successfully added to your watch list.\n \n" + "These are the brands that you are currently looking out for: \n" + answer)
    else:
      bot.reply_to(message, f"{name.title()} is already in your watch list!")
  except IndexError:
    bot.send_message(chatID, "You might have forgotten to enter the brand after the /addbrand command. Try again.")
  
@bot.message_handler(commands=["watchlist"])
def viewList(message):
  # returns all the items in watchList to the user in the form of a numbered list
  global watchList
  if watchList:
    answer = listToNumberedList()
    bot.reply_to(message, answer)
  else:
    bot.reply_to(message, "Your list is currently empty. To add brands to your watch list, use /addbrand insert-brand-here.")

@bot.message_handler(commands=["clearlist"])
def clearWatchList(message):
  global watchList
  watchList = []
  bot.reply_to(message, "Your watch list has been emptied. You are not looking out for any brands right now. To add brands to your watch list, use /addbrand insert-brand-here.")

@bot.message_handler(commands=["remove"])
def removeItem(message):
  #removes the particular brand from the user's watchList
  global watchList
  try:
    name = extract_arg(message.text)
    if name in watchList:
      watchList.remove(name.lower())
      answer = listToNumberedList()
      bot.reply_to(message, f"{name.title()} has been successfully removed from your watchlist.\n \n" + "These are the brands that you are currently looking out for: \n" + answer)
    else:
      bot.reply_to(message, f"You cant remove {name.title()} because it wasn't even in your watch list to begin with!")
  except IndexError:
    bot.send_message(chatID, "You might have forgotten to enter the brand after the /remove command. Try again.")

@bot.message_handler(commands=["hmu"])
def hitmeup(message):
  #feed users any deals from the past 7 days
  global forum
  global watchList
  global flag
  flag = True
  titlesScanned = []
  if forum and bool(watchList): # checks if there is a forum defined and if there is anything in the watchlist
    bot.send_message(chatID, "Looking for deals...")
    while forum and watchList and flag:
      for submission in submissionsWithinAWeek(forum): # 7 day period brand in watchList: 
        bot.send_message(chatID, f"{submission.title}")
        if flag:
          for brand in watchList:
            title = submission.title.lower().split() #title is now an array of words
            if (brand in title) and (submission.title.lower() not in titlesScanned) and flag:
              try:
                titlesScanned.append(submission.title.lower())
                title = html.escape(submission.title or '')
                user = html.escape(submission.author.name or '')
                body = html.escape(submission.selftext or '')
                link = html.escape(submission.url or '')

                template = "{title}\n{body}\n{link}\nby {user}"
                messageText = template.format(title=title, body=body, link=link, user=user)
                bot.send_message(chat_id=chatID, text=messageText)
                sleep(3)
              except ResponseException:
                bot.send_message(chatID, "Oops, there seem to be an error when retrieving deals. Trying again in 5 seconds.")
                sleep(5)
              # how and when do i want to stop?
              except Exception:
                bot.send_message(chatID, "Oops, something it wrong")
        else:
          break
  else:
    bot.send_message(chatID, "It seems like you have not set your gender or have not added brands into your watch list for me to look out for. " + 
            "To set your gender, use /male or /female. To add brands to your watch list, use /addbrand your-brand-here.")

@bot.message_handler(commands=["stop"])
def stopFeeding(message):
  #stop feeding deals to user
  global flag
  flag = False
  bot.reply_to(message, "I'll stop feeding you deals. You can use /hmu again if you want me to start feeding you deals again")

bot.polling()
