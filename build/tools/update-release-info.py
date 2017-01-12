#!/usr/bin/env python3
#+
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

import os
import sys
import shutil
import inspect
from dsl import load_profile_config
from utils import e , info

dsl = load_profile_config()

def main():
    source = e('${PROFILE_ROOT}/release')
    destination = e('${BUILD_ROOT}/release')

    # Delete the ./release directory thus removing current content
    if os.path.exists(destination):
        shutil.rmtree(destination)

    # Copy the complete profile/release directory to ./release
    # thus recreating ./release with the up-to-date content
    shutil.copytree(source, destination)

if __name__ == '__main__':
    info('Updating Release Information')
    sys.exit(main())
