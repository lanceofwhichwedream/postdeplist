# postdeplist
Easy deployment list posting to deployment flow

REQUIRES Python 3.2+, Python 2.x will not work.

Usage: ./postdeplist [-f | --filter <filter id>] [-l | --list <deploylist.txt>]

	<filter_id> is a JIRA filter ID from the Deploy List link.

	<deploylist.txt> is any text file containg one or more deploy items,
	separated by a single empty line or '--'' on a line by itself.
