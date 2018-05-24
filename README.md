# postdeplist
Easy deployment list posting to deployment flow

REQUIRES Python 3.2+, Python 2.x will not work.

Installation of required Python modules:

	pip install -r requirements.txt

Required Modules:

- Requests (`pip install requests`)
- JIRA (`pip install jira`)

Usage:

	./postdeplist [-f | --filter \<filter id\>] [-l | --list \<deploylist.txt\>]

	Where <filter_id> is a JIRA filter ID from the Deploy List link.

	Where <deploylist.txt> is any text file containg one or more deploy items,
	separated by a single empty line or '--'' on a line by itself.
