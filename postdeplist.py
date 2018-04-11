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

"""
Simple application to post deploys list to Flowdock.

Works with a plain text file and a JIRA filter ID.

REQUIRES Python3, will not function with Python 2.x.

Author: Chris Gatewood <chris.gatewood@icg360.com>
"""

__AUTHOR__ = 'Chris Gatewood <chris.gatewood@icg360.com>'

# ##### VARIABLES ##### #

# SET THE FLOW HERE TO WHATEVER FLOW WE'RE POSTING THIS LIST TO
flow = "test"
username = "TeamAwesome"

# SET THE URL FOR JIRA
jira_url = 'https://icg360.atlassian.net/'

#########################


def readFileList(depFile):
  """
  Reads a DEP list from a plain-text file and returns the list to be iterated
  through.
  """

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


def readDepList(filter_id, user, passwd):
  """
  Reads a DEP list from a JIRA CM ticket and returns a sorted list to be
  iterated through.
  """

  global jira_url

  # Establish connection to JIRA
  jac = JIRA(server=jira_url, basic_auth=(user, passwd))

  # Set the filter from the CLI argument
  filter_query = jac.filter(filter_id)

  # Perform the search and return the result list
  results = jac.search_issues(filter_query.jql)

  depList = []
  for result in results:
    # Looks at the "Deploy Time" field to filter deploys that do not happen
    # at 9PM Eastern
    if result.fields.customfield_10305:
      dep_date = datetime.strptime(result.fields.customfield_10305,
        "%Y-%m-%dT%H:%M:%S.%f%z")

      if dep_date.date() == date.today() and dep_date.hour == 21:
        # Append if the field is not blank and contains today's date and
        # 9PM ET time
        depList.append(jira_url + 'browse/' + result.key + ' - ' +
            result.fields.summary)
    else:
      # Append if the field is left blank also
      depList.append(jira_url + 'browse/' + result.key + ' - ' +
        result.fields.summary)

  # Return a sorted list (DBADMIN first, then DEP)
  return sorted(depList)


def processList(depList, config):
  """
  processList loops through the deploy list that was returned by either the
  plain-text file or JIRA CM ticket functions
  """

  for dep in depList:
    postToFD(dep, config['fd_user'], config['fd_pass'])


def postToFD(post, user, passwd):
  """
  postToFD() posts the list item to the Flowdock flow as specified in global
  var "flow". It will also make use of a global var for a user name as
  specified in the global var "username".

  TODO: Prompt and store the user name to send
  TODO: Prompt with a list of available flows and store selection
  """
  global flow, username

  userpass = user + ":" + passwd  # Holds user + pass in Basic Auth format
  url = "https://api.flowdock.com/flows/icg/" + flow + "/messages"
  headers = {
    "Authorization": "Basic " + base64.b64encode(userpass.encode()).decode(),
    "Content-Type": "application/json"
  }

  post = post + "  " + date.strftime(date.today(), "#%b_%d_deploy").lower()

  payload = {
    "event": "message",
    "content": post,
    "external_user_name": username
    }

  resp = requests.post(url, headers=headers, json=payload)

  if response.status_code == 201:
    print(post, "-", "Success!")
  else:
    print(post, "-", "Failed!\n")
    print(response.json())


def getConfigPath():
  """
  getConfigpath determines the appropriate location for postdeplist's config
  file for the current OS (should function for Win/Mac/Linux) and returns that
  path to caller
  """

  if 'APPDATA' in os.environ:
    path = os.path.join(os.environ['APPDATA'], 'icgdeplist.cfg')
  elif 'XDG_CONFIG_HOME' in os.environ:
    path = os.path.join(
      os.environ['XDG_CONFIG_HOME'], 'icgdeplist.cfg')
  else:
    path = os.path.join(
      os.environ['HOME'], '.config', 'icgdeplist.cfg')

  return path


def readConfig():
  """
  Read in the config file for postdeplist. This file contains the username
  and passwords for both Flowdock and JIRA
  """

  configpath = getConfigPath()

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
  """
  Prompts the user for username and password to Flowdock and JIRA and stores
  the resulting values in a local configuration file which will be read on all
  subsequent instances of the program being run.
  """

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

  configpath = getConfigPath()

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
  parser.add_argument('-l', '--list',
    help='Deploy List file\nEntries separated by "--" or empty lines')
  args = parser.parse_args()

  if args.filter or args.list:
    config = readConfig()
    if config is False:
      config = writeConfig()

    if args.filter:
      depList = readDepList(args.filter,
        config['jira_user'],
        config['jira_pass'])

    if args.list:
      depList = readFileList(args.list)

    if depList is not False:
      processList(depList, config)

  else:
    usage = """[-f | --filter <filter id>] [-l | --list <deploylist.txt>]

    <filter_id> is a JIRA filter ID from the Deploy List link.

    <deploylist.txt> is any text file containg one or more deploy items,
    separated by a single empty line or '--' on a line by itself.
    """

    print("Usage: ", sys.argv[0], usage)
    sys.exit(1)
