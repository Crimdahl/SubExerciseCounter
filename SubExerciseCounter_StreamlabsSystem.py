# -*- coding: utf-8 -*-

# Importing Required Libraries
import sys

sys.platform = "win32"
import codecs, json, os, re, io, threading, datetime, clr, math

clr.AddReference("IronPython.Modules.dll")
clr.AddReferenceToFileAndPath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "References",
                                           "TwitchLib.PubSub.dll"))
from TwitchLib.PubSub import TwitchPubSub
from datetime import datetime, timedelta

#   Script Information <Required>
ScriptName = "SubExerciseCounter"
Website = "https://www.twitch.tv/Crimdahl"
Description = "Tracks a count of subscription-related exercises."
Creator = "Crimdahl"
Version = "1.1.2"

#   Define Global Variables <Required>
script_path = os.path.dirname(__file__)
settings_path = os.path.join(script_path, "settings.json")
readme_path = os.path.join(script_path, "Readme.md")
log_file = os.path.join(script_path, "script_log.txt")
script_settings = None
exercises = {}

twitch_event_receiver = None
twitch_event_receiver_queue = []
thread = None
tick_timer = datetime.now() + timedelta(minutes=5)
attempt_reconnect = True


# Define Settings. If there is no settings file created, then use default values in else statement.
class Settings(object):
    def __init__(self, settings_path=None):
        if settings_path and os.path.isfile(settings_path):
            with codecs.open(settings_path, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
            if not hasattr(self, "presets"):
                self.presets = {}
        else:
            # General Settings
            self.run_only_when_live = False
            self.command_name = "exercise"

            # Output Settings
            self.debug_level = "Info"
            self.enable_logging_to_file = True

            # Command Settings
            self.command_permissions = "Moderator"

            # Subscription Settings
            self.reconnect_interval = 5
            self.client_id = "l6xhpee6j3ddawvg8wnol71sg832l6"
            self.twitch_oauth_token = ""
            self.response_on_subscription = ""
            self.subscription_exercise_type = "Burpees"
            self.subscription_exercise_increment = 1

            # Internal Settings
            self.presets = {}

    def Reload(self, jsondata):
        log("Settings reloaded.",
            LoggingLevel.str_to_int.get("Info"))
        self.__dict__ = json.loads(jsondata, encoding="utf-8")
        return

    def Save(self, settings_path):
        try:
            with codecs.open(settings_path, encoding="utf-8-sig", mode="w+") as f:
                json.dump(self.__dict__, f, encoding="utf-8")
        except:
            log("Failed to save settings to the file. Fix error and try again",
                LoggingLevel.str_to_int.get("Fatal"))
        return


class LoggingLevel:
    str_to_int = {
        "All": 1,
        "Debug": 2,
        "Info": 3,
        "Warn": 4,
        "Fatal": 5,
        "Nothing": 6
    }
    int_to_string = {
        1: "All",
        2: "Debug",
        3: "Info",
        4: "Warn",
        5: "Fatal",
        6: "Nothing"
    }

    def __str__(self):
        return str(self.value)


#   Process messages <Required>
def Execute(data):
    if str(data.GetParam(0)).lower() == "!" + script_settings.command_name:
        if script_settings.run_only_when_live and not Parent.IsLive():
            return

        user_id = get_user_id(data.RawData)
        if Parent.HasPermission(data.User, script_settings.command_permissions, "") or user_id == "216768170":
            if data.GetParamCount() == 1:
                # Display current exercises
                global exercises
                if len(exercises) == 0:
                    post("You have no exercises in the queue.")
                else:
                    response = "Exercises in your queue: "
                    for k, v in exercises.items():
                        response = response + str(v) + " " + str(k) + ", "
                    post(response[:len(response) - 2] + ".")
                return
            else:
                subcommand = data.GetParam(1)

            if subcommand == "add" or subcommand == "sub":
                # Command should look like: !command [add or sub] [integer] (exercise type)
                #   Adds/subtracts the amount and type of exercise
                if data.GetParamCount() >= 2:
                    arguments = [item.strip() for item in data.Message[data.Message.rindex(data.GetParam(1)) +
                                                                       len(data.GetParam(1)) + 1:].split("|")]
                    try:
                        # Feed the remaining arguments to function to return a dictionary of new exercises
                        new_exercises = get_exercises_as_dict(arguments)

                        global exercises
                        for exercise_type, v in new_exercises.items():
                            if subcommand == "sub":
                                # If we're subtracting, invert the supplied number
                                new_exercises[exercise_type] = 0 - abs(int(v))
                        modify_exercises_with_dict(new_exercises)
                        return
                    except ValueError as e:
                        # Command was supplied an invalid value.
                        log(str(e), LoggingLevel.str_to_int.get("Warn"))
                        pass
                # If the command has reached this point, there was a problem. Display the command usage in chat.
                if subcommand == "add":
                    post("Command usage: ![command name] add [integer] (exercise type)(| [integer] (exercise type))...")
                elif subcommand == "sub":
                    post("Command usage: ![command name] sub [integer] (exercise type)(| [integer] (exercise type))...")
                return
            elif subcommand == "reset" or subcommand == "clear":
                # Command should look like: !command reset (exercise type)
                #   Clears the supplied exercise, or all exercises if no argument is supplied
                global exercises
                if data.GetParamCount() >= 3:
                    # An exercise type was supplied. Get the exercise from the message.
                    exercise_type = data.Message[data.Message.rindex(data.GetParam(1)) +
                                                 len(data.GetParam(1)) + 1:].title()

                    # Remove the exercises if they exist
                    if exercise_type in exercises.keys():
                        exercises.pop(exercise_type)
                    else:
                        log("Reset subcommand was supplied an exercise type that did not exist: " +
                            str(exercise_type), LoggingLevel.str_to_int.get("Warn"))

                    # Regardless of the outcome, I send a success message
                    post(str(exercise_type).title() + " have been cleared.")
                    return
                else:
                    # No exercise type was supplied. Clear the exercises dictionary.
                    exercises = {}
                    post("All exercises have been cleared.")
                    return
            elif subcommand == "preset" or subcommand == "presets":
                if data.GetParamCount() > 2:
                    arguments = [item.strip() for item in data.Message[data.Message.rindex(data.GetParam(1)) +
                                                                       len(data.GetParam(1)) + 1:].split("|")]
                    presets_not_found = []
                    for preset in arguments:
                        if preset in script_settings.presets.keys():
                            modify_exercises_with_dict(script_settings.presets[preset])
                        else:
                            presets_not_found.append(str(preset))
                    if len(presets_not_found) > 0:
                        post("No presets were found for '" + "' and '".join(presets_not_found) + "'.")
                else:
                    if len(script_settings.presets) > 0:
                        available_presets = []
                        for preset in script_settings.presets.keys():
                            available_presets.append(preset)
                        available_presets.sort()
                        post("Available presets: " + ", ".join(available_presets))
                    else:
                        post("There are no saved presets.")
            elif subcommand == "addpreset":
                # Command should look like: !command addpreset [Preset Name] [Preset Exercises]
                if data.GetParamCount() >= 3:
                    try:
                        new_preset = data.GetParam(2)
                        new_exercise_dict = get_exercises_as_dict(data.Message[data.Message.rindex(data.GetParam(2)) +
                                                                               len(data.GetParam(2)) + 1:].split("|"))

                        global settings_path
                        script_settings.presets[new_preset] = new_exercise_dict
                        script_settings.Save(settings_path)
                        post("Preset '" + new_preset + "' saved.")
                        return
                    except ValueError as e:
                        # Command was supplied an invalid first argument.
                        log("preset subcommand was supplied an invalid argument: " +
                            str(e), LoggingLevel.str_to_int.get("Warn"))
                        pass
                    # Insufficient arguments supplied
                    post("Command usage: ![command name] addpreset [preset name] [integer] [exercise type]"
                         "(| [integer] [exercise type)...")

            elif subcommand == "delpreset":
                if data.GetParamCount() == 3:
                    try:
                        script_settings.presets.pop(data.GetParam(2))
                        script_settings.Save(settings_path)
                        post("Preset deleted.")
                        return
                    except KeyError as e:
                        post("No preset by that name exists.")
                        return
                    # Insufficient arguments supplied
                    post("Command usage: ![command name] delpreset [preset name]")
            elif subcommand == "?" or subcommand == "help":
                post("Available subcommands: add, sub, reset, clear, preset, addpreset, delpreset.")

        else:
            post("Sorry, " + data.UserName + ", you do not have permission to use that command.")
            log(data.UserName + " has insufficient permissions to use that command.",
                LoggingLevel.str_to_int.get("Warn"))
        return


#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
def Tick():
    # Every x minutes, attempt to connect to Twitch
    global tick_timer
    if tick_timer <= datetime.now():
        tick_timer = datetime.now() + timedelta(minutes=script_settings.reconnect_interval)
        global twitch_event_receiver
        if twitch_event_receiver is None:
            post("ExerciseCounter is attempting to reconnect to the channel to listen for subscriptions.")
            Start()

    global thread
    if thread and not thread.isAlive():
        thread = None

    if not thread and len(twitch_event_receiver_queue) > 0:
        log("Starting new thread. " + str(datetime.now()),
            LoggingLevel.str_to_int.get("Debug"))
        thread = twitch_event_receiver_queue.pop(0)
        thread.start()

    return


#   Reload settings and receiver when clicking Save Settings in the Chatbot
def ReloadSettings(jsonData):
    log("Saving settings.", LoggingLevel.str_to_int.get("Info"))
    global twitch_event_receiver
    try:
        # Reload settings
        script_settings.__dict__ = json.loads(jsonData)
        script_settings.Save(settings_path)

        Unload()
        Start()
        log("Settings saved successfully", LoggingLevel.str_to_int.get("Info"))
    except Exception as e:
        log(str(e), LoggingLevel.str_to_int.get("Fatal"))

    return


#   Init called on script load. <Required>
def Init():
    # Initialize Settings
    global script_settings
    script_settings = Settings(settings_path)
    script_settings.Save(settings_path)

    log("Exercise tracking script loaded.", LoggingLevel.str_to_int.get("Debug"))
    # Initialize Receiver
    Start()
    return


def Start():
    log("Starting receiver", LoggingLevel.str_to_int.get("Debug"))

    global twitch_event_receiver
    twitch_event_receiver = TwitchPubSub()
    twitch_event_receiver.OnPubSubServiceConnected += EventReceiverConnected
    twitch_event_receiver.OnChannelSubscription += EventReceiverNewSubscription
    twitch_event_receiver.OnPubSubServiceClosed += EventReceiverDisconnected
    twitch_event_receiver.Connect()
    return


def EventReceiverConnected(sender, e):
    log("Event receiver connecting.", LoggingLevel.str_to_int.get("Debug"))
    #  Get Channel ID for Username
    headers = {
        "Client-ID": script_settings.client_id,
        "Authorization": "Bearer " + script_settings.twitch_oauth_token
    }
    result = json.loads(Parent.GetRequest("https://api.twitch.tv/helix/users?login=" +
                                          Parent.GetChannelName(), headers))

    if "error" in result.keys():
        if result["error"] == "Unauthorized":
            post("ExerciseCounter is not authorized to listen for subscriptions on this channel. "
                 "Please ensure you have a valid oAuth key in the script settings.")
        else:
            post("ExerciseCounter: Error connecting to channel. See logs for details.")
            log("oAuth connection attempt error: " + str(result["error"]), LoggingLevel.str_to_int.get("Fatal"))

    log("Result of oAuth connection attempt: " + str(result), LoggingLevel.str_to_int.get("Debug"))

    if "error" in result.keys():
        # The receiver failed to connect. Delete the object so the script can retry later.
        log("ExerciseCounter Error connecting to channel: " +
            str(result["error"]), LoggingLevel.str_to_int.get("Fatal"))
        global twitch_event_receiver
        twitch_event_receiver = None
        return

    user = json.loads(result["response"])
    user_id = user["data"][0]["id"]

    log("Connection to Twitch channel " + Parent.GetChannelName() +
        " established. Now listening for new subscriptions.",
        LoggingLevel.str_to_int.get("Info"))

    twitch_event_receiver.ListenToSubscriptions(user_id)
    twitch_event_receiver.SendTopics(script_settings.twitch_oauth_token)
    post("ExerciseCounter: Connection to Twitch channel '" + Parent.GetChannelName() +
         "' established.")
    return


def EventReceiverDisconnected(sender, e):
    if e:
        post("ExerciseCounter: Connection to Twitch lost. See logs for error message.")
        log("Disconnect error: " + str(e), LoggingLevel.str_to_int.get("Fatal"))


def EventReceiverNewSubscription(sender, e):
    log("Event receiver received new subscription notification.",
        LoggingLevel.str_to_int.get("Info"))

    twitch_event_receiver_queue.append(threading.Thread(target=NewSubscriptionWorker))


def NewSubscriptionWorker():
    log("New subscription received. Incrementing exercise count.",
        LoggingLevel.str_to_int.get("Info"))
    global exercises
    exercise_amount = script_settings.subscription_exercise_increment
    if int(exercise_amount) > 0:
        exercise_type = script_settings.subscription_exercise_type
        if exercise_type in exercises.keys():
            exercises[exercise_type] = exercises[exercise_type] + int(exercise_amount)
        else:
            exercises[exercise_type] = int(exercise_amount)

    if not script_settings.response_on_subscription == "":
        message = script_settings.response_on_subscription
        message = message.replace("$channel", Parent.GetChannelName())
        message = message.replace("$exercise", script_settings.subscription_exercise_type)
        message = message.replace("$count", str(exercises[exercise_type]))
        post(message)
    return


def Unload():
    # Disconnect EventReceiver cleanly
    try:
        global twitch_event_receiver
        if twitch_event_receiver:
            twitch_event_receiver.Disconnect()
            twitch_event_receiver = None
    except:
        log("Event receiver already disconnected", LoggingLevel.str_to_int.get("Warn"))
    return


#   Opens readme file <Optional - DO NOT RENAME>
def open_readme():
    os.startfile(readme_path)
    return


#   Opens Twitch.TV website to ask permissions
def GetToken():
    os.startfile("https://id.twitch.tv/oauth2/authorize?response_type=token&client_id=" + script_settings.client_id +
                 "&redirect_uri=https://twitchapps.com/tokengen/&scope=channel:read:subscriptions&force_verify=true")
    return


#   Helper method to log
def log(message, level=LoggingLevel.str_to_int.get("All")):
    if script_settings.enable_logging_to_file:
        global log_file
        file = open(log_file, "a+")
        file.writelines(str(datetime.now()).ljust(26) + " " + str(LoggingLevel.int_to_string.get(level) + ":").ljust(
            10) + message + "\n")
        file.close()
    if LoggingLevel.str_to_int.get(script_settings.debug_level) <= level:
        Parent.Log(ScriptName, "(" + str(LoggingLevel.int_to_string.get(level)) + ") " + message)


#   Helper method to post to Twitch Chat
def post(message):
    Parent.SendStreamMessage(message)


def get_user_id(raw_data):
    # Retrieves the user ID of a Twitch chatter using the raw data returned from Twitch
    try:
        raw_data = raw_data[raw_data.index("user-id=") + len("user-id="):]
        raw_data = raw_data[:raw_data.index(";")]
    except Exception:
        return ""
    return raw_data


def get_exercises_as_dict(data):
    exercise_dict = {}
    for exercise in data:
        # The first value supplied should be the amount of the exercise as an integer
        exercise = exercise.strip()
        exercise_amount = exercise[:exercise.index(" ")]
        if not float(exercise_amount).is_integer():
            raise ValueError("The supplied exercise amount was not an integer.")

        # Do nothing if the exercise supplied had a count of 0
        if not exercise_amount == 0:
            exercise_type = exercise[exercise.index(" ") + 1:].title()
            if exercise_type == "":
                # If the exercise type was not supplied, use the subscription exercise type
                if script_settings.subscription_exercise_type == "":
                    raise ValueError("No exercise type was supplied and Subscription Exercise Type is not configured.")
                exercise_type = script_settings.subscription_exercise_type.title()
            exercise_dict[exercise_type] = exercise_amount
    return exercise_dict


def modify_exercises_with_dict(new_exercises):
    global exercises
    popped = []
    incremented = []
    decremented = []
    did_not_exist = []
    response = ""
    for exercise_type, exercise_amount in new_exercises.items():
        if exercise_type in exercises.keys():
            # If we're decrementing an exercise and it removes all of that exercise, remove the
            #   exercise from the dictionary
            if (int(exercise_amount) < 0
                    and abs(int(exercise_amount)) >= int(exercises[exercise_type])):
                exercises.pop(exercise_type)
                popped.append(exercise_type)
            else:
                exercises[exercise_type] = exercises[exercise_type] + int(exercise_amount)
                if int(exercise_amount) > 0:
                    incremented.append(exercise_type)
                else:
                    decremented.append(exercise_type)
        else:
            if int(exercise_amount) > 0:
                exercises[exercise_type] = int(exercise_amount)
                incremented.append(exercise_type)
            else:
                did_not_exist.append(exercise_type)
    if len(incremented) > 0:
        response = response + " and ".join(incremented) + " were added to the queue. "
    if len(decremented) > 0:
        response = response + " and ".join(decremented) + " were subtracted from the queue. "
    if len(popped) > 0:
        response = response + " and ".join(popped) + " were eliminated from the queue. "
    if len(did_not_exist) > 0:
        response = response + " and ".join(did_not_exist) + " did not exist in the queue."
    if not response == "":
        post(response)


