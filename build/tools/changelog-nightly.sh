#!/bin/sh

make-changelog() {
        rm -f ChangeLog
        rm -f /tmp/changes.$$
        echo "## Git commits in last 24 hours (nightly build)" > /tmp/changes.$$
        for repo in ${BE_ROOT}/*; do
		if [ ! -d ${repo}/.git ]; then continue ; fi

		git --git-dir=${repo}/.git log --oneline --since yesterday > /tmp/_changes.$$
		if [ -s /tmp/_changes.$$ ]; then
			echo "### Repository `basename ${repo}`" >> /tmp/changes.$$
			cat /tmp/_changes.$$ >> /tmp/changes.$$
			rm -f /tmp/_changes.$$
		fi
        done
        cat /tmp/changes.$$ > ChangeLog
        rm -f /tmp/changes.$$
        CHANGELOG=`realpath ChangeLog`
}

if [ -z "$BE_ROOT" ] ; then
   echo "Missing BE_ROOT"
   exit 1
fi
make-changelog
