#-
# Copyright 2010-2016 The FreeNAS Project
# All rights reserved
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted providing that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# This Software is Provided by the Author ''As Is'' and Any Express or
# Implied Warranties, Including, But Not Limited To, the Implied
# Warranties of Merchantability and Fitness For a Particular Purpose
# Are Disclaimed.  In No Event Shall the Author be Liable For Any
# Direct, Indirect, Incidental, Special, Exemplary, or Consequential
# Damages (Including, But Not Limited To, Procurement of Substitute
# Goods or Services; Loss of Use, Data, or Profits; or Business
# Interruption) However Caused And on Any Theory of Liability, Whether
# in Contract, Strict Liability, or Tort (Including Negligence or
# Otherwise) Arising in Any Way Out of the Use of This Software, Even
# if Advised of the Possibility of Such Damage.
#
######################################################################

.ifndef BUILD_TIMESTAMP
BUILD_TIMESTAMP != date -u '+%Y%m%d%H%M'
.endif
BUILD_STARTED != date '+%s'

BUILD_ROOT ?= ${.CURDIR}
BUILD_CONFIG := ${BUILD_ROOT}/build/config
BUILD_TOOLS := ${BUILD_ROOT}/build/tools
PYTHONPATH := ${BUILD_ROOT}/build/lib
MK := ${MAKE} -f ${BUILD_ROOT}/Makefile.inc1

PROFILE_SETTING = ${BUILD_ROOT}/build/profiles/profile-setting
.ifndef PROFILE
. if exists(${PROFILE_SETTING})
PROFILE != cat ${PROFILE_SETTING}
. else
PROFILE := freenas
. endif
.endif

GIT_REPO_SETTING = ${BUILD_ROOT}/.git-repo-setting
.if exists(${GIT_REPO_SETTING})
GIT_LOCATION != cat ${GIT_REPO_SETTING}
.endif

BE_ROOT := ${BUILD_ROOT}/${PROFILE}/_BE

OBJDIR := ${BE_ROOT}/objs
API_PATH := ${BE_ROOT}/freenas/docs

.if exists(${BUILD_ROOT}/.git-ref-path)
GIT_REF_PATH != cat ${BUILD_ROOT}/.git-ref-path
.elif exists(/build/gitrefs)
GIT_REF_PATH ?= /build/gitrefs
.endif

.export BUILD_TIMESTAMP
.export BUILD_STARTED

.export BUILD_ROOT
.export BUILD_CONFIG
.export BUILD_TOOLS
.export PYTHONPATH
.export MK

.export PROFILE
.export SDK
.export BUILD_SDK

.export GIT_REPO_SETTING
.export GIT_LOCATION

.export BE_ROOT
.export OBJDIR
.export API_PATH

.export GIT_REF_PATH

.export BUILD_LOGLEVEL

.BEGIN:
# make(.Target) is a conditional that evalutes to true if the .TARGET
# was specified on the command line or has been declared the default
# .Target (either explicitly or implicity) somewhere before this line
.if !make(remote) && !make(sync) && !make(bootstrap-pkgs)
	@echo "[0:00:00] ==> NOTICE: Selected profile: ${PROFILE}"
	@echo "[0:00:00] ==> NOTICE: Build timestamp: ${BUILD_TIMESTAMP}"

	@${BUILD_TOOLS}/buildenv.py ${BUILD_TOOLS}/check-host.py
.if !make(checkout) && !make(update) && !make(clean) && !make(cleandist) && !make(profiles) && !make(select-profile) && !make(docs) && !make(api-docs)
	@${BUILD_TOOLS}/buildenv.py ${BUILD_TOOLS}/check-sandbox.py
.endif
.endif

# The following section is where the Recipes and other items that are
# to be built are denoted regardless of dependency states.  This is to
# say that if the .Target is "release" the release files will be built
# (re-built) regardless of whether they have have been changed or not.
.PHONY: release ports tests

buildenv:
	@${BUILD_TOOLS}/buildenv.py sh

bootstrap-pkgs:
	pkg install -y archivers/pxz
	pkg install -y lang/python3
	pkg install -y lang/python
	pkg install -y ports-mgmt/poudriere-devel
	pkg install -y devel/git
	pkg install -y devel/gmake
	pkg install -y archivers/pigz
	python -m ensurepip
	python -m pip install six

changelog-nightly:
	@${BUILD_TOOLS}/changelog-nightly.sh


# The .DEFAULT gets run if there is no Recipe denoted above for the
# .Target (this includes release, ports, and tests) the only
# difference between these and others is that the others are only
# built if they or one of their dependencies has been changed
.DEFAULT:
	@mkdir -p ${OBJDIR}
	@${BUILD_TOOLS}/buildenv.py ${MK} ${.TARGET}
