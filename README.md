# Flag Tracking Script

This script detects subscriptions and counts the number of exercises you have to do.

## Installing

This script was built for use with Streamlabs Chatbot.
Follow instructions on how to install custom script packs at:
https://github.com/StreamlabsSupport/Streamlabs-Chatbot/wiki/Prepare-&-Import-Scripts

Once installed you will need to provide a Client ID and an oAuth token. You can get a Client ID by registering the app under one of your accounts. My (Crimdahl) Client ID is supplied by default. You can receive an oAuth token by clicking the Get Token button in script settings.
This button also exists in the streamlabs chatbot UI. Make sure you don't show this token on stream, it is as sensitive
as your stream key!

## Use
### Options
-Accept Commands Only When Live: Toggles the ability to respond to chat commands when offline. (Default: False)

-Command Name: The name of the base command. Commands are invoked with !command subcommand. If you were to set this variable to "fitness", you would add 10 pushups by using the following: "!fitness add 10 pushups" (Default: Burpees)

-Command Permissions: Sets the permissions required for a chatter to use the commands. (Default: Moderator)

-Subscription Exercise Type: The type of exercise you wish to increment when receiving a subscription. (No Default)

-Subscription Exercise Increment: How many of the exercise you want to do after each subscription. (Default: 1)

-Response on Subscription: The chat message to display after receiving a subscription. Empty = no message. Substitues "$channel" for your channel name, "$exercise" for your Subscription Exercise Type, and "$count" for the current number of your Subscription Exercise Type now in the queue. (Default: "")

-Twitch Client ID: The Client ID received when registering the App. (Default: l6xhpee6j3ddawvg8wnol71sg832l6)

-Twitch oAuth Token: Your Twitch oAuth token to authenticate the redemption listener. (No default)

-Auto-reconnection Interval: How long, in minutes, does the script go between auto reconnection attempts? (Default: 5)

-Level of Chatbot Logging: Choose verbosity of chatbot logging. Higher levels include all lower levels. (Default: Info)

-Enable File Logging: If enabled, will log all levels of logging to script_log.txt in the script directory in addition to the Streamlabs Chatbot script log, useful for later reference. (Default: True)


### Commands
All commands begin with an exclamation mark, followed by your configured command name.

-![Command Name]
Using just the base command will display all of the exercises currently in your queue.

-![Command Name] add [Integer] (Exercise Type)
Adds the number of the specified exercise type to the queue. If no exercise type is supplied, it will add to your configured Subscription Exercise Type.

-![Command Name] sub [Integer] (Exercise Type)
Subtracts the number of the specified exercise type, if it exists. If no exercise type is supplied, it will subtract from your configured Subscription Exercise Type. If the new number of that exercise is equal or less than 0, the exercise is removed from the queue completely.

-![Command Name] [reset/clear] (Exercise Type)
Removes the specified exercise type from the queue, if it exists. If no exercise type is supplied, clears the entire exercise queue.

-![Command Name] Uptime
Displays the length of time the script has been connected to Twitch

-![Command Name] reconnect
Attempt to manually reconnect the script to your channel.


## Authors

Crimdahl - [Twitch](https://www.twitch.tv/crimdahl), [Twitter](https://www.twitter.com/crimdahl)

IceyGlaceon - [Twitch](https://www.twitch.tv/iceyglaceon), [Twitter](https://www.twitter.com/theiceyglaceon)

## References

This script makes use of TwitchLib's pubsub listener to detect the channel point redemptions. Go check out their repo at https://github.com/TwitchLib/TwitchLib for more info.

This script is based off of [IceyGlaceon's ChannelPointstoChannelCurrency script.](https://github.com/iceyglaceon/SLCB-Channel-Points-to-Channel-Currency/blob/master/ChannelPointsToChannelCurrency.zip?raw=true)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
