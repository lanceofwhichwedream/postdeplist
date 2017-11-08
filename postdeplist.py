#!/usr/bin/python

import requests
import base64
import sys
import os

try:
    import ConfigParser as configparser
except:
    import configparser

'''
Simple program to post list of Deploys from text file into
Deployment flow of Flowdock

Author: Chris Gatewood <chris.gatewood@icg360.com>
'''


# Reads DEP list from file and returns list to be iterated through
def readList(depFile):
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


# Posts the DEP list that was read in via iteration
def postList(depList, user, passwd, flow):
    userpass = user + ":" + passwd  # Holds user + pass in Basic Auth format
    url = "https://api.flowdock.com/flows/icg/" + flow + "/messages"
    headers = {
        "Authorization": "Basic " + base64.b64encode(userpass.encode()).decode(),
        "Content-Type": "application/json"
    }

    for dep in depList:
        payload = {"event": "message", "content": dep}
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
    appconfig['user'] = config.get('general', 'username')
    appconfig['pass'] = config.get('general', 'password')

    return appconfig


def writeConfig():
    try:
        username = raw_input('Please enter your Flowdock username: ')
    except NameError:
        username = input('Please enter your Flowdock username: ')

    try:
        password = raw_input('Please enter your Flowdock password: ')
    except NameError:
        password = password('Please enter your Flowdock password: ')

    config = configparser.RawConfigParser()
    config.add_section('general')
    config.set('general', 'username', username)
    config.set('general', 'password', password)

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
    appconfig['user'] = username
    appconfig['pass'] = password

    return appconfig


if __name__ == "__main__":

    # SET THE FLOW HERE TO WHATEVER FLOW WE'RE POSTING THIS LIST TO
    flow = "test"
    ###################################

    if len(sys.argv) == 2:
        config = readConfig()
        if config is False:
            config = writeConfig()

        depList = readList(sys.argv[1])
        postList(depList, config['user'], config['pass'], flow)

    else:
        print("Usage: ", sys.argv[0], "<deploylist.txt>")
        print("\n<deploylist.txt> is any text file containg one or more deploy items,")
        print("separated by a single empty line or -- on a line by itself.")
        quit(1)
