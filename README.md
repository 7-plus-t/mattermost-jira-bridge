# JIRA Webhook Bridge for Mattermost

This repository contains a Python Flask application that accepts webhooks from [JIRA
Server](https://www.atlassian.com/software/jira) and forwards them to the specified
channel, or channels, in a [Mattermost](https://mattermost.com) server via an incoming webhook.
You can configure the application to post to channels based on JIRA projects and issue type
as described below in the **Configuration** section or provide the target channel name in the webhook directly (see [JIRA Webhook section](#JIRA Webhook)).

Currently the application supports the following JIRA event types:

* Project Created
* Issue Created
* Issue Edited
* Issue Commented
* Issue Comment - Edited
* Issue Comment - Deleted

 
 **Import Notes**:
 * This application has only been tested with JIRA Server 7.9.2. 
 * This application was written extremely quickly and could use additional work in the form of refactoring, the addition of error handling, and testing (including on different versions of JIRA). Please feel free to jump in and help with pull requests, issues, etc.
 * This application is an example of how to bridge JIRA webhooks to Mattermost and is not 
 meant to be used in a production environment.

# Installation, Configuration, and Execution

The following section describes how to install, configure and run the Flask application.

## Installation

The easiest way to install this application is to:

1. Log into the machine that will host the Python Flask application;
2. Clone this repository to your machine: `git clone https://github.com/cvitter/mattermost-jira-bridge.git`;
3. Create a webhook in Mattermost to accept posts from JIRA (**Note**: You will need the URL for
this webhook when configuring the application below.)

## Configuration

Once the application has been cloned it needs to be configured for your environment and
how your organization uses JIRA. The following instructions cover configuration:

1. Change directories to the application's root: `cd mattermost-jira-bridge`;
2. Make a copy of `config.sample` as `config.json`: `cp config.sample config.json`
3. Open the `config.json` file using your favorite editor (e.g. `sudo nano config.json`) and make the
edits to each section as described below:

**Application**

The `application` section setups up the runtime environment of the Flask application. For most uses
you can leave this as-is or simply update the port to the desired port for your environment.

```
	"application" : {
		"host" : "0.0.0.0",
		"port" : 5007,
		"debug" : false
	}
```

If you do not want the Flask application to be accessible from other machines you can 
update the host address to `127.0.0.1`. You can also enable Flask's debug mode by 
changing `debug` to `true`.

**Features**

The `features` section allows you to configure how messages map to Mattermost channels based 
on JIRA project and whether or not the issue is labeled as a bug. The channel mapping has
the following options:


* All messages are sent to the default channel configured in the Mattermost webhook;
* Messages are mapped to Mattermost channels based on mappings in the `projects.json` file;
* Messages are mapped to Mattermost channels based on a naming pattern configured in the 
`project_to_channel_pattern` setting.

Specific configuration settings are described in more detail below.

```
	"features" : {
		"use_project_to_channel_map" : true,
		"use_project_bugs_to_channel_map" : true,
		"use_project_to_channel_pattern" : true,
		"project_to_channel_pattern" : "jira-", 
		"use_bug_specific_channel" : false,
		"bug_channel_postfix" : "-bugs",
		"use_attachments" : true
	}
```

* `use_project_to_channel_map` - when set to `true` the application will check the `projects.json`
file and select the Mattermost channel based on the JIRA Project Key. In the example file
below the `PRJX` project key would map to the `prjx-jira' channel in Mattermost.

```
{
	"projects" : {
    		"prjx": "prjx-jira",
    		"prjx-bug": "prjx-jira-bugs",
    		"prjz": "prjz-jira"
	}
}
```

**Note**: In the example above the `prjx-jira` channel is named `PRJX: JIRA`. Mattermost converted 
the channel name to `prjx-jira` for the channel URL by replacing spaces with `-` and removing 
special characters. When specifying the channel to send messages to you need to use this
modified URL friendly format. If you need to find the correct format you can select `View Info` 
for the channel in Mattermost and select the channel portion of the URL, e.g.:
`https://mymattermostserver.com/myteam/channels/prjx-jira`.

**Important Note**: If no channel is specified Mattermost will post the message into the default
channel configured in the webhook. If a channel _is_ specified but does not exist in
Mattermost the message will not post in Mattermost.

* `use_project_bugs_to_channel_map` - when set to true the application will check the `projects.json`
file when the issue type equals `bug` and select the Mattermost channel based on the JIRA Project 
Key with `-bug` appended to it. In the example above a bug submitted in the PRJX project
would be mapped as `prjx-bug` and the corresponding message would be posted to the 
`prjx-jira-bugs` channel.

* `use_project_to_channel_pattern` - when set to `true` the application will prepend the value found
in the `project_to_channel_pattern` field to the project key to generate the channel name to post
the message to. 

**Note**:  This setting will work if both `use_project_to_channel_map` and 
`use_project_bugs_to_channel_map` are set to `true`. In scenarios where the project key being tested 
does not have a match in the `projects.json` folder the application will try and match the message 
to a folder based on the `project_to_channel_pattern` field.

**Important Note**: Once `use_project_to_channel_pattern` is set to `true` the application will try to
send all messages to channels based on the `project_to_channel_pattern` (if the channel name isn't
created using the Project to Channel Mapping). If the channel doesn't exist in Mattermost the
message will not post. 
 
* `project_to_channel_pattern` - the string to prepend to the project key to generate a channel name
to post a message to.

* `use_bug_specific_channel` - when set to `true` the application will append the `bug_channel_postfix` value
to the channel name. 

* `bug_channel_postfix` - The value appended to the channel name if `use_bug_specific_channel` is set 
to `true`. The default value is `-bugs`.

* `use_attachments` - when set to `true` the application sends messages in the Mattermost 
[Message Attachment](https://docs.mattermost.com/developer/message-attachments.html) format. When
set to `false` messages will be sent as plain text (with Markdown support).


**Colors**

The `colors` section has one setting, `attachment`,  which sets the highlight color
of the message if sent as a 
[Message Attachment](https://docs.mattermost.com/developer/message-attachments.html).
**Note**: The default color that the application ships with is green.

```
	"colors" : {
		"attachment" : "#28c12b"
	}
```

**Mattermost**

The `mattermost` section is used to configure the Mattermost web hook that the application
will post messages to. You can optionally add a user name and icon to override the 
default configured in Mattermost.

```
	"mattermost" : {
		"webhook" : "https://mattermost.url/hooks/webhookid",
		"post_user_name" : "JIRA",
		"post_user_icon" : ""
	}
```

**JIRA**

The `jira` section has one setting for the base URL of your JIRA server. This setting is used
to generate links in messages the application posts to Mattermost.

```
	"jira" : {
		"url" : "http://jira.url:8080/"
	}
```

### JIRA Webhook

The following steps describe how to setup the JIRA webhook:

1. Select `System` from the `Administration` menu (**Note**: You must have administrative rights.)
2. Click on `WebHooks` in the `Advanced` section.
3. Click on the `Create a WebHook` button at the top right of the page.
4. Fill in the `New WebHook Listener` form:
    * Enter a name for your webhook;
    * Click on `Enabled` for `Status` to ensure that the webhook fires;
    * Webhook URL:
		* If project to channel mapping is used, enter the address of your running bridge application and append `/${project.key}` to the end 
      (example:` https://bridge.url/jira/${project.key}`) so that JIRA will pass
      the project key via the URL to bridge application.
		* If the channel is configured in the webhook, enter the address of the bridge application and append `/channel/<channel name>`
		(example: `https://bridge.url/jira/channel/town-square`)
    * Select the events that you want to send from JIRA to Mattermost (**Note**: only the
      events listed in the introduction above are currently supported however unsupported
      events will not cause application failures.)
5. Click on the `Create` button to finish creating the webhook.


## Execution

Once the application is configured that are a number of ways to run it. The simplest for 
testing purposes is:

`sudo python jira.py`

For longer term execution I use the following command that runs the application headlessly 
and captures output into a log file for troubleshooting:

```
sudo python jira.py >> jira.log 2>&1 &
```


# Make this Project Better (Questions, Feedback, Pull Requests Etc.)

**Help!** If you like this project and want to make it even more awesome please contribute your ideas,
code, etc.

If you have any questions, feedback, suggestions, etc. please submit them via issues here: https://github.com/cvitter/mattermost-jira-bridge/issues

If you find errors please feel to submit pull requests. Any help in improving this resource is appreciated!

# License
The content in this repository is Open Source material released under the MIT License. Please see the [LICENSE](LICENSE) file for full license details.

# Disclaimer

The code in this repository is not sponsored or supported by Mattermost, Inc.

# Authors
* Author: [Craig Vitter](https://github.com/cvitter)

# Contributors 

Please submit Issues and/or Pull Requests.
