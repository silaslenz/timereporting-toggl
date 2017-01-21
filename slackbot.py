#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
from slackclient import SlackClient
import json
import requests
import create_report

with open('config.json') as data_file:
    config = json.load(data_file)

# constants
AT_BOT = "<@" + config["slack_botID"] + ">"
EXAMPLE_COMMAND = "do"
BOT_NAME = 'togglbot'

slack_client = SlackClient(config["slack_key"])


class SlackBot:
    def __init__(self):
        self.report_text = ""

    def handle_command(self, command, channel):
        """
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        """
        if command.startswith("report"):
            file_name = create_report.generate_report(self.report_text)
            slack_client.api_call("files.upload", filename=file_name, channels=channel, file=open("full.pdf", "rb"))
        else:
            response = "Use *report* to get latest report. Upload a text snippet named report to generate new report."
            slack_client.api_call("chat.postMessage", channel=channel, text=response, as_user=True)

    def parse_slack_output(self,slack_rtm_output):
        """
            The Slack Real Time Messaging API is an events firehose.
            this parsing function returns None unless a message is
            directed at the Bot, based on its ID.
        """
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
#                print(output)
                if output and 'text' in output and AT_BOT in output['text']:
                    # return text after the @ mention, whitespace removed
                    return output['text'].split(AT_BOT)[1].strip().lower(), \
                           output['channel']
                # Message was a file and that file was intended for bot (report.txt).
                if output and "file" in output and "name" in output["file"] and output["file"]["name"] == "report.txt":
                    # Save file. Use file to generate report and send file
                    report = requests.get(output["file"]["url_private_download"], headers={'Authorization': "Bearer " + config["slack_key"]})
                    report.encoding = "uft-8"
                    self.report_text = report.text
                    file_name = create_report.generate_report(self.report_text)
                    slack_client.api_call("files.upload", filename=file_name, channels=output['channel'], file=open("full.pdf", "rb"))
        return None, None

    def main(self):
        READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
        if slack_client.rtm_connect():
            print("StarterBot connected and running!")
            while True:
                command, channel = self.parse_slack_output(slack_client.rtm_read())
                if command and channel:
                    self.handle_command(command, channel)
                time.sleep(READ_WEBSOCKET_DELAY)
        else:
            print("Connection failed. Invalid Slack token or bot ID?")

slack_bot = SlackBot()
slack_bot.main()
