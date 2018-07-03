from flask import Flask
from flask import request
import json
import requests
import events
import projects


def read_config():
    """
    Reads config.json to get configuration settings
    """
    d = json.load(open('config.json'))

    global application_host, application_port, application_debug
    application_host = d["application"]["host"]
    application_port = d["application"]["port"]
    application_debug = d["application"]["debug"]

    global use_project_to_channel_map, use_project_to_channel_pattern
    global project_to_channel_pattern, use_attachments
    use_project_to_channel_map = d["features"]["use_project_to_channel_map"]
    use_project_to_channel_pattern = d["features"]["use_project_to_channel_pattern"]
    project_to_channel_pattern = d["features"]["project_to_channel_pattern"]
    use_attachments = d["features"]["use_attachments"]

    global attachment_color
    attachment_color = d["colors"]["attachment"]

    global webhook_url, mattermost_user, mattermost_icon
    webhook_url = d["mattermost"]["webhook"]
    mattermost_user = d["mattermost"]["post_user_name"]
    mattermost_icon = d["mattermost"]["post_user_icon"]

    global jira_url
    jira_url = d["jira"]["url"]


def get_channel(project_id):
    """
    Returns the Mattermost channel to post into based on
    settings in config.json or returns "" if not configured
    """
    channel = ""
    if use_project_to_channel_map:
        channel = projects.project_list.get(project_id, "")
    if use_project_to_channel_pattern and len(channel) == 0:
        channel = project_to_channel_pattern + project_id
    return channel


def send_webhook(project_id, text):
    """
    Sends the formatted message to the configured
    Mattermost webhook URL
    """
    if len(project_id) > 0:
        channel = get_channel(project_id)

    data = {
        "channel": channel,
        "username": mattermost_user,
        "icon_url": mattermost_icon
    }

    if use_attachments:
        data["attachments"] = [{
            "color": attachment_color,
            "text": text
        }]
    else:
        data["text"] = text

    response = requests.post(
        webhook_url,
        data=json.dumps(data),
        headers={'Content-Type': 'application/json'}
    )
    return response


def user_profile_link(user_id, user_name):
    return "[" + user_name + "](" + jira_url + \
        "secure/ViewProfile.jspa?name=" + user_id + ")"


def project_link(project_name, project_id):
    return "[" + project_name + "](" + jira_url + "projects/" + \
        project_id + ")"


def issue_link(project_id, issue_id):
    return "[" + issue_id + "](" + jira_url + "projects/" + \
        project_id + "/issues/" + issue_id + ")"


def format_new_issue(event, project_id, issue_key, summary, description,
                     priority):
    return "" + \
        event + " " + issue_link(project_id, issue_key) + "\n" \
        "**Summary**: " + summary + " (_" + priority + "_)\n" \
        "**Description**: " + description


def format_changelog(changelog_items):
    """
    The changelog can record 1+ changes to an issue
    """
    output = ""
    if len(changelog_items) > 1:
        output = "\n"
    for item in changelog_items:
        output += "Field **" + item["field"] + "** updated from _" + \
                  str(item["fromString"]) + "_ to _" + \
                  str(item["toString"]) + "_\n"
    return output


def format_message(project_id, project_name, event, user_id, user_name):
    """
    """
    message = "" + \
        "**Project**: " + project_link(project_id, project_id) + "\n" \
        "**Action**: " + event + "\n" \
        "**User**: " + user_profile_link(user_id, user_name)
    return message


def handle_actions(project_id, data):
    """
    """
    message = ""

    jira_event = data["webhookEvent"]
    jira_event_text = events.jira_events.get(jira_event, "")
    issue_type = ""

    if len(jira_event_text) == 0:
        """
        Not a supported JIRA event, return None
        and quietly go away
        """
        return None

    if jira_event == "project_created":
        message = format_message(project_id, data["project"]["name"],
                                 jira_event_text,
                                 data["project"]["projectLead"]["key"],
                                 data["project"]["projectLead"]["displayName"])

    if jira_event.find("issue") > -1:
        issue_type = data["issue"]["fields"]["issuetype"]["name"]
        print ("Issue Type: " + issue_type)

    if jira_event == "jira:issue_created":
        message = format_message(project_id,
                                 data["issue"]["fields"]["project"]["name"],
                                 format_new_issue(jira_event_text, project_id,
                                                  data["issue"]["key"],
                                                  data["issue"]["fields"]["summary"],
                                                  data["issue"]["fields"]["description"],
                                                  data["issue"]["fields"]["priority"]["name"]),
                                 data["user"]["key"],
                                 data["user"]["displayName"])

    if jira_event == "jira:issue_updated":
        issue_event_type = data["issue_event_type_name"]
        if issue_event_type == "issue_generic" or issue_event_type == "issue_updated":
            message = format_message(project_id,
                                     data["issue"]["fields"]["project"]["name"],
                                     "**Issue**: " + issue_link(project_id, data["issue"]["key"]) + "\n" + \
                                       format_changelog(data["changelog"]["items"]),
                                     data["user"]["key"],
                                     data["user"]["displayName"])

        if issue_event_type == "issue_commented" or issue_event_type == "issue_comment_edited" or issue_event_type == "issue_comment_deleted":
            message = format_message(project_id,
                                     data["issue"]["fields"]["project"]["name"],
                                     format_changelog(data["changelog"]["items"]),
                                     data["user"]["key"],
                                     data["user"]["displayName"])

        if issue_event_type == "issue_comment_edited" or issue_event_type == "issue_comment_deleted":

            message = ""

    return send_webhook(project_id, message)


"""
------------------------------------------------------------------------------------------
Flask application below
"""
read_config()

app = Flask(__name__)


@app.route('/jira/<project_id>', methods=['POST'])
def hooks(project_id):

    if len(request.get_json()) > 0:
        print(project_id)
        print(json.dumps(request.get_json()))

        handle_actions(project_id, request.get_json())
    return ""

if __name__ == '__main__':
    app.run(host=application_host, port=application_port,
            debug=application_debug)
