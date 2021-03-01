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
-Accept Commands Only When Live: Toggles the ability to respond to chat commands when offline. (Default: True)

-Command Permissions: Sets the permissions required for a chatter to use the commands. (Default: Moderator)

-Count Command Name: Customizes the command used to display and modify your queue. (No Default)

-Reset Command Name: Customizes the command used to display and modify your queue. (No Default)

-Type of Exercise: The type of exercise you wish to do after subs. (No Default)

-Increment Per Sub: How much of the exercise you want to do after each sub. (Default: 1)

-Twitch Client ID: The Client ID received when registering the App. (Default: l6xhpee6j3ddawvg8wnol71sg832l6)

-Twitch oAuth Token: Your Twitch oAuth token to authenticate the redemption listener. (No default)

-Enable Responses: Toggles the ability to post responses to your command directly in Twitch chat. (Default: True)

-Enable Debug: Toggles the ability to post debug messages in the Chatbot Logs. (Default: True)

### Commands
-!<CountCommandName>: Displays the number of exercises you have pending.
  
-!<ResetCommandName>: Resets your pending exercise count to 0.

## Authors

Crimdahl - [Twitch](https://www.twitch.tv/crimdahl), [Twitter](https://www.twitter.com/crimdahl)

IceyGlaceon - [Twitch](https://www.twitch.tv/iceyglaceon), [Twitter](https://www.twitter.com/theiceyglaceon)

## References

This script makes use of TwitchLib's pubsub listener to detect the channel point redemptions. Go check out their repo at https://github.com/TwitchLib/TwitchLib for more info.

This script is based off of [IceyGlaceon's ChannelPointstoChannelCurrency script.](https://github.com/iceyglaceon/SLCB-Channel-Points-to-Channel-Currency/blob/master/ChannelPointsToChannelCurrency.zip?raw=true)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
