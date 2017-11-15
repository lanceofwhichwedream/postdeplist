#!/usr/bin/env python3

import requests
import base64
import sys
import os
import configparser
import argparse
from jira import JIRA
from datetime import datetime, date
from getpass import getpass
'''
Simple application to post deploys list to Flowdock.

Works with a plain text file, and a JIRA filter ID.

REQUIRES Python3, will not function with Python 2.x.

Author: Chris Gatewood <chris.gatewood@icg360.com>
'''

__AUTHOR__ = 'Chris Gatewood <chris.gatewood@icg360.com>'

# ##### VARIABLES ##### #

# SET THE FLOW HERE TO WHATEVER FLOW WE'RE POSTING THIS LIST TO
flow = "test"

# SET THE URL FOR JIRA
jira_url = 'https://icg360.atlassian.net/'

#########################


# Reads DEP list from file and returns list to be iterated through
def readFileList(depFile):
    depList = []  # Initialize a blank list
    depLines = ""  # Initialize blank string

    f = open(depFile, "r")

    for line in f:
        if line == '--\n' or line == '\n':
            depList.append(depLines)
            depLines = ""  # Empty depLines for next DEP
        else:
            depLines += line

    # Catch the last DEP in list if for loop was broken before the last append
    if depList[:-1] != depLines:
        depList.append(depLines)

    return depList


# Reads DEP list from JIRA and returns the list to be iterated through
def readDepList(filter_id, user, passwd):
    global jira_url

    jac = JIRA(server=jira_url, basic_auth=(user, passwd))
    filter_query = jac.filter(filter_id)
    results = jac.search_issues(filter_query.jql)

    depList = []
    for result in results:
        if result.fields.customfield_10305:
            dep_date = datetime.strptime(result.fields.customfield_10305, "%Y-%m-%dT%H:%M:%S.%f%z")
            if dep_date.date() == date.today():
                # Append if the field is not blank and contains today's date
                depList.append(jira_url + 'browse/' + result.key + ' - ' + result.fields.summary)
        else:
            # Append if the field is blank
            depList.append(jira_url + 'browse/' + result.key + ' - ' + result.fields.summary)

    return sorted(depList)


# This function loops through the deploy list created by either function above and
# pushes to Flowdock returning the response code.
def processList(depList, config):
    for dep in depList:
        postToFD(dep, config['fd_user'], config['fd_pass'])


# Posts the DEP list that was read in via iteration
def postToFD(post, user, passwd):
    global flow

    userpass = user + ":" + passwd  # Holds user + pass in Basic Auth format
    url = "https://api.flowdock.com/flows/icg/" + flow + "/messages"
    headers = {
        "Authorization": "Basic " + base64.b64encode(userpass.encode()).decode(),
        "Content-Type": "application/json"
    }

    payload = {"event": "message", "content": post}
    resp = requests.post(url, headers=headers, json=payload)
    print(resp)


# Read config file
def readConfig():
    if 'APPDATA' in os.environ:
        configpath = os.path.join(os.environ['APPDATA'], 'icgdeplist.cfg')
    elif 'XDG_CONFIG_HOME' in os.environ:
        configpath = os.path.join(
            os.environ['XDG_CONFIG_HOME'], 'icgdeplist.cfg')
    else:
        configpath = os.path.join(
            os.environ['HOME'], '.config', 'icgdeplist.cfg')

    config = configparser.RawConfigParser()
    config.read(configpath)

    if len(config.sections()) == 0:
        return False

    appconfig = {}
    appconfig['fd_user'] = config.get('fd', 'username')
    appconfig['fd_pass'] = config.get('fd', 'password')

    appconfig['jira_user'] = config.get('jira', 'username')
    appconfig['jira_pass'] = config.get('jira', 'password')

    return appconfig


def writeConfig():
    fd_username = input('Please enter your Flowdock username: ')
    fd_password = getpass('Please enter your Flowdock password: ')

    jira_username = input('Please enter your JIRA username: ')
    jira_password = getpass('Please enter your JIRA password: ')

    config = configparser.RawConfigParser()

    config.add_section('fd')
    config.set('fd', 'username', fd_username)
    config.set('fd', 'password', fd_password)

    config.add_section('jira')
    config.set('jira', 'username', jira_username)
    config.set('jira', 'password', jira_password)

    if 'APPDATA' in os.environ:
        configpath = os.path.join(os.environ['APPDATA'], 'icgdeplist.cfg')
    elif 'XDG_CONFIG_HOME' in os.environ:
        configpath = os.path.join(
            os.environ['XDG_CONFIG_HOME'], 'icgdeplist.cfg')
    else:
        configpath = os.path.join(
            os.environ['HOME'], '.config', 'icgdeplist.cfg')

    with open(configpath, 'w') as configfile:
        config.write(configfile)

    appconfig = {}
    appconfig['fd_user'] = fd_username
    appconfig['fd_pass'] = fd_password
    appconfig['jira_user'] = jira_username
    appconfig['jira_pass'] = jira_password

    return appconfig


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter', help='JIRA Filter ID')
    parser.add_argument('-l', '--list', help='Deploy List Text file.\nEntries separated by "--" or empty lines')
    args = parser.parse_args()

    if args.filter or args.list:
        config = readConfig()
        if config is False:
            config = writeConfig()

        if args.filter:
            depList = readDepList(args.filter, config['jira_user'], config['jira_pass'])

        if args.list:
            depList = readFileList(args.list)

        if depList is not False:
            processList(depList, config)

    else:
        usage = '''[-f | --filter <filter id>] [-l | --list <deploylist.txt>]

        <filter_id> is a JIRA filter ID from the Deploy List link.

        <deploylist.txt> is any text file containg one or more deploy items,
        separated by a single empty line or '--'' on a line by itself.
        '''

        print("Usage: ", sys.argv[0], usage)
        quit(1)
