import requests
from datetime import datetime
from pylatex import Document, Section, Subsection, Tabular, Command, base_classes, NoEscape
import json

with open('config.json') as data_file:    
    config = json.load(data_file)


geometry_options = {"tmargin": "1cm", "lmargin": "1cm"}
doc = Document(geometry_options=geometry_options, documentclass =  Command('documentclass', options=base_classes.Options('a4paper'), arguments='article'))


def extract_time(json):
    try:
        return (json['user'], json["start"])
    except KeyError:
        return 0


def iso_time_to_datetime(time_str):
    k = time_str.rfind(":")
    time_str = time_str[:k] + time_str[k+1:]
    return datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S%z')


if __name__ == '__main__':
    detailed_report = requests.get('https://toggl.com/reports/api/v2/details', params={'user_agent': config["user_agent"], 'workspace_id': config["workspace_id"]}, auth=(config["api_tokens"][0], "api_token")).json()["data"]
    detailed_report.sort(key=extract_time, reverse=False)  # Sort first by user and then by start time

    with doc.create(Subsection('Tidsrapport')):
        doc.preamble.append(NoEscape("\definecolor{Gray}{gray}{0.9}"))
        with doc.create(Tabular('|l|p{5cm}|l|l|l|')) as table:
            rowcolor = "white"
            lastuser = ""
            table.add_hline()

            for event in detailed_report:
                # Toggle color between users
                if lastuser != event["user"]:
                    lastuser = event["user"]
                    if rowcolor == "white":
                        rowcolor = "lightgray"
                    else:
                        rowcolor = "white"

                start_time = iso_time_to_datetime(event["start"])
                end_time = iso_time_to_datetime(event["end"])

                table.add_row([event["user"], event["description"], start_time.strftime("%a %Y-%m-%d kl. %H:%M"), end_time.strftime("%a %Y-%m-%d kl. %H:%M"), end_time-start_time], color=rowcolor)
                table.add_hline()

    doc.generate_pdf('full', clean_tex=False)