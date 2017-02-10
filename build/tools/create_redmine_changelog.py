#!/usr/local/bin/python3

import sys
import getopt
import re
import unicodedata
from redmine import Redmine, exceptions


def main(argv):
    key = ''
    project = ''
    target = 'SU Candidate'
    stat = 'Ready For Release'
    s = None
    include_tracker = False
    helpmesg = "create_redmine_changelog.py -k <key> -p <project> -s <status>"
    priority_order = "Blocks Until Resolved,Regression,Critical,Expected,Important,Nice to have,No priority"
    try:
        opts, args = getopt.getopt(argv, "hmik:p:t:s:r:", ["key=", "project=", "target=", "status=", "--include_tracker", "--priority_order"])
    except getopt.GetoptError:
        print(helpmesg)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(helpmesg)
            sys.exit(2)
        elif opt in ("-k", "--key"):
            key = arg
        elif opt in ("-p", "--project"):
            project = arg
        elif opt in ("-t", "--target"):
            target = arg
        elif opt in ("-s", "--status"):
            stat = arg
        elif opt in ("-i", "--include_tracker"):
            include_tracker = True
        elif opt in ("-o", "--priority_order"):
            priority_order = arg
    if key == '':
        print("<key> cannot be blank")
        sys.exit(2)
    if project == '':
        print("<project> cannot be blank")
        sys.exit(2)
    project = project.lower()
    priority_order = priority_order.split(",")

    bugs = 'https://bugs.freenas.org'

    rm = Redmine(bugs, key=key)

    statuses = rm.issue_status.all()
    for status in statuses:
        if str(status) == stat:
            s = status
            break

    if s:
        issues = rm.issue.filter(status_id=s.id)
    else:
        print("{0} status does not exist or server is unreachable".format(stat))
        sys.exit(2)

    entrytext = ''
    entries = {}

    for issue in reversed(issues):
        ticketnum = str(issue.id)
        priority = str(issue.priority)
        if priority not in entries.keys():
            entries[priority] = []
        entrytext = issue.subject
        tracker = str(issue.tracker)
        skip = False
        proj = str(issue.project).lower()
        try:
            if str(issue.fixed_version) != target:
                if proj == project:
                    sys.stderr.write(
                        "WARNING: {0}/issues/{1} is set to {2} not to {3}\n".format(
                            bugs, ticketnum, issue.fixed_version, target)
                    )
                skip = True
        except exceptions.ResourceAttrError:
            sys.stderr.write(
                "WARNING: {0}/issues/{1} target version is not set\n".format(bugs, ticketnum)
            )
            skip = True

        if project == 'freenas' and proj == 'truenas':
            skip = True
        elif project == 'freenas-10' and proj != project:
            skip = True
        else:
            try: 
                for field in issue.custom_fields:
                    if str(field) == "ChangeLog Entry":
                        if field.value:
                            if 'hide this' not in field.value.lower():
                                if project == 'truenas' and 'freenas only' in field.value.lower():
                                    skip = True
                                else:
                                    entrytext = field.value
                            else:
                                skip = True
            except exceptions.ResourceAttrError:
                continue
            if not skip:
                entrytext = re.sub('freenas\s*only:?', '', entrytext, flags=re.IGNORECASE).strip()
                if include_tracker:
                    fmt = "* {0}\t{1}\t{2}"
                    entrytext = re.sub('\n', '\n\t\t', entrytext)
                    try:
                        entry = fmt.format(ticketnum, tracker, entrytext)
                    except UnicodeError:
                        entrytext = unicodedata.normalize('NFKD', entrytext).encode('ascii', 'ignore')
                        entry = fmt.format(ticketnum, tracker, entrytext)

                else:
                    fmt = "* {0}\t{1}"
                    entrytext = re.sub('\n', '\n\t', entrytext)
                    try:
                        entry = fmt.format(ticketnum, entrytext)
                    except UnicodeError:
                        entrytext = unicodedata.normalize('NFKD', entrytext).encode('ascii', 'ignore')
                        entry = fmt.format(ticketnum, entrytext)
                entries[priority].append(entry)

    for priority in priority_order:
        if priority in entries: 
            tickets = entries[priority]
            if len(tickets) > 0:
                print("## {0}".format(priority))
                for ticket in tickets:
                    print(ticket)


if __name__ == "__main__":
    main(sys.argv[1:])
