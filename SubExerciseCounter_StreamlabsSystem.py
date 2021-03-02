# -*- coding: utf-8 -*-

# Importing Required Libraries
import sys
sys.platform = "win32"
import codecs, json, os, re, io, threading, datetime, clr, math
clr.AddReference("IronPython.Modules.dll")
clr.AddReferenceToFileAndPath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "References", "TwitchLib.PubSub.dll"))
from TwitchLib.PubSub import TwitchPubSub

#   Script Information <Required>
ScriptName = "SubExerciseCounter"
Website = "https://www.twitch.tv/Crimdahl"
Description = "Tracks a count of subscription-related exercises."
Creator = "Crimdahl"
Version = "1.1.0"

#   Define Global Variables <Required>
ScriptPath = os.path.dirname(__file__)
SettingsPath = os.path.join(ScriptPath, "settings.json")
ReadmePath = os.path.join(ScriptPath, "Readme.md")
ScriptSettings = None
ExerciseCount = 0

EventReceiver = None
ThreadQueue = []
Thread = None
PlayNextAt = datetime.datetime.now()

# Define Settings. If there is no settings file created, then use default values in else statement.
class Settings(object):
    def __init__(self, SettingsPath=None):
        if SettingsPath and os.path.isfile(SettingsPath):
            with codecs.open(SettingsPath, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        else:
            #Output Settings
            self.EnableDebug = True
            self.EnableChatResponses = True
            self.EnableChatPermissionErrors = True
            self.EnableChatLiveErrors = False
            self.EnableSubscriptionThanks = False
            self.ThankYouMessage = "Thank you for the subscription! $channel's $exercise count is now at $count."
            self.RunCommandsOnlyWhenLive = True

            #Command Settings
            self.CommandPermissions = "Moderator"
            self.ExerciseType = "burpee"
            self.IncrementAmount = 1
            self.CountCommandName = "burpeecount"
            self.ResetCommandName = "burpeereset"

            #Twitch Settings
            self.ClientID = "l6xhpee6j3ddawvg8wnol71sg832l6"
            self.TwitchOAuthToken = ""

    def Reload(self, jsondata):
        self.__dict__ = json.loads(jsondata, encoding="utf-8")
        return

    def Save(self, SettingsPath):
        try:
            with codecs.open(SettingsPath, encoding="utf-8-sig", mode="w+") as f:
                json.dump(self.__dict__, f, encoding="utf-8")
        except:
            Log("Failed to save settings to the file. Fix error and try again")
        return

#   Process messages <Required>
def Execute(data):
    if data.Message == "!" + ScriptSettings.CountCommandName:
        if ScriptSettings.RunCommandsOnlyWhenLive and not Parent.IsLive():
            if ScriptSettings.EnableChatLiveErrors: Post("Command ignored: the channel is currently offline.")
            if ScriptSettings.EnableDebug: Log("Command ignored: the channel is currently offline.")
        elif not Parent.HasPermission(data.User, ScriptSettings.CommandPermissions, ""):
            if ScriptSettings.EnableChatPermissionErrors: Post("Sorry, " + data.UserName + ", you do not have permission to use the Count command.")
            if ScriptSettings.EnableDebug: Log(data.UserName + " has insufficient permissions to use the Count command.")
        else:
            global ExerciseCount
            Post("Your current " + ScriptSettings.ExerciseType + " count from subscriptions is " + str(ExerciseCount) + ".")
            if ScriptSettings.EnableDebug: Log("Count command called. " + str.capitalize(ScriptSettings.ExerciseType) + " count is " + str(ExerciseCount) + ".")
    elif data.Message == "!" + ScriptSettings.ResetCommandName:
        if ScriptSettings.RunCommandsOnlyWhenLive and not Parent.IsLive():
            if ScriptSettings.EnableChatLiveErrors: Post("Command ignored: the channel is currently offline.")
            if ScriptSettings.EnableDebug: Log("Command ignored: the channel is currently offline.")
        elif not Parent.HasPermission(data.User, ScriptSettings.CommandPermissions, ""):
            if ScriptSettings.EnableChatPermissionErrors: Post("Sorry, " + data.UserName + ", you do not have permission to use the Reset command.")
            if ScriptSettings.EnableDebug: Log(data.UserName + " has insufficient permissions to use the Reset command.")
        else:
            global ExerciseCount
            ExerciseCount = 0
            if ScriptSettings.EnableChatResponses: Post(str.capitalize(ScriptSettings.ExerciseType) + " count reset.")
            if ScriptSettings.EnableDebug: Log("Reset command called. " + ScriptSettings.ExerciseType + " count reset.")
    return

#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
def Tick():
    global PlayNextAt
    if PlayNextAt > datetime.datetime.now():
        return

    global Thread
    if Thread and Thread.isAlive() == False:
        Thread = None

    if Thread == None and len(ThreadQueue) > 0:
        if ScriptSettings.EnableDebug: Log("Starting new thread. " + str(PlayNextAt))
        Thread = ThreadQueue.pop(0)
        Thread.start()

    return
    
#   Reload settings and receiver when clicking Save Settings in the Chatbot
def ReloadSettings(jsonData):
    if ScriptSettings.EnableDebug: Log("Saving settings.")
    global EventReceiver
    try:
        #Reload settings
        ScriptSettings.__dict__ = json.loads(jsonData)
        ScriptSettings.Save(SettingsPath)

        Unload()
        Start()
        if ScriptSettings.EnableDebug: Log("Settings saved successfully")
    except Exception as e:
        if ScriptSettings.EnableDebug: Log(str(e))

    return

#   Init called on script load. <Required>
def Init():
    #Initialize Settings
    global ScriptSettings
    ScriptSettings = Settings(SettingsPath)
    ScriptSettings.Save(SettingsPath)

    if ScriptSettings.EnableDebug: Log("Exercise tracking script loaded.")
    #Initialize Receiver
    Start()
    return

def Start():
    if ScriptSettings.EnableDebug: Log("Starting receiver")

    global EventReceiver
    EventReceiver = TwitchPubSub()
    EventReceiver.OnPubSubServiceConnected += EventReceiverConnected
    EventReceiver.OnChannelSubscription += EventReceiverNewSubscription

    EventReceiver.Connect()
    return

def EventReceiverConnected(sender, e):
    if ScriptSettings.EnableDebug: Log("Event receiver connecting")
    #  Get Channel ID for Username
    headers = {
        "Client-ID": ScriptSettings.ClientID,
        "Authorization": "Bearer " + ScriptSettings.TwitchOAuthToken
    }
    result = json.loads(Parent.GetRequest("https://api.twitch.tv/helix/users?login=" + Parent.GetChannelName(), headers))
    if ScriptSettings.EnableDebug: Log("result: " + str(result))
    user = json.loads(result["response"])
    id = user["data"][0]["id"]

    if ScriptSettings.EnableDebug: Log("Event receiver connected, sending topics for channel id: " + id)

    EventReceiver.ListenToSubscriptions(id)
    EventReceiver.SendTopics(ScriptSettings.TwitchOAuthToken)
    return

def EventReceiverNewSubscription(sender, e):
    if ScriptSettings.EnableDebug: Log("Event receiver received new subscription notification.")

    ThreadQueue.append(threading.Thread(target=NewSubscriptionWorker))

def NewSubscriptionWorker():
    if ScriptSettings.EnableDebug: Log("New subscription received. Incrementing exercise count.")
    global ExerciseCount
    ExerciseCount = ExerciseCount + ScriptSettings.IncrementAmount
    if ScriptSettings.EnableSubscriptionThanks:
        message = ScriptSettings.ThankYouMessage
        message = message.replace("$channel", Parent.GetChannelName())
        message = message.replace("$exercise", ScriptSettings.ExerciseType)
        message = message.replace("$count", str(ExerciseCount))
        Post(message)

    global PlayNextAt
    PlayNextAt = datetime.datetime.now() + datetime.timedelta(0, 0)
    return

def Unload():
    # Disconnect EventReceiver cleanly
    try:
        global EventReceiver
        if EventReceiver:
            EventReceiver.Disconnect()
            EventReceiver = None
    except:
        if ScriptSettings.EnableDebug: Log("Event receiver already disconnected")

    return

#   Opens readme file <Optional - DO NOT RENAME>
def openreadme():
    os.startfile(ReadmePath)
    return

#   Opens Twitch.TV website to ask permissions
def GetToken(): 
    os.startfile("https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=" + ScriptSettings.ClientID + "&redirect_uri=https://twitchapps.com/tokengen/&scope=channel:read:subscriptions&force_verify=true")
    return

#   Helper method to log
def Log(message): 
    Parent.Log(ScriptName, message)

#   Helper method to post to Twitch Chat
def Post(message):
    Parent.SendStreamMessage(message)

def GetAttribute(attribute, message):
    # if str(message).index(str(attribute)) > -1:
        attribute = attribute.lower() + ":"
        #The start index of the attribute begins at the end of the attribute designator, such as "game:"
        try:
            index_of_beginning_of_attribute = message.lower().index(attribute) + len(attribute)
        except ValueError as e:
            raise e
        #The end index of the attribute is at the last space before the next attribute designator, or at the end of the message
        try:
            index_of_end_of_attribute = message[index_of_beginning_of_attribute:index_of_beginning_of_attribute + message[index_of_beginning_of_attribute:].index(":")].rindex(" ")
        except ValueError:
            #If this error is thrown, the end of the message was hit, so just return all of the remaining message
            return message[index_of_beginning_of_attribute:].strip()
        return message[index_of_beginning_of_attribute:index_of_beginning_of_attribute + index_of_end_of_attribute].strip().strip(",")
    # else:
    #     raise AttributeError(str(attribute) + " was not found in the supplied information.")