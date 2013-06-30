#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import time
from appscript import *
from tempfile import mkstemp
from shutil import move
from os import remove, close
import argparse
import base64


from wowapi.battlenet import BattleNet
from wowapi.wowlogin import ACCOUNT_NAMES
from wowapi.wowlogin import CHAR_NAMES
from wowapi.wow import KEY_ENTER
from wowapi.wowlogin import WorldOfWarcraftLogin

PROFESSION_CDS = [("Tailoring","Imperial Silk",["/use Silkworm Cocoon"]),
("Inscription","Scroll of Wisdom",[]),
("Inscription","Northrend Inscription Research",[]),
("Alchemy","Transmute: Living Steel",[]),
("Jewelcrafting","Imperial Amethyst",["/use Facets of Research"]),
("Jewelcrafting","Primordial Ruby",["/use Facets of Research"]),
("Jewelcrafting","River's Heart",["/use Facets of Research"]),
("Jewelcrafting","Sun's Radiance",["/use Facets of Research"]),
("Jewelcrafting","Vermillion Onyx",["/use Facets of Research"]),
("Jewelcrafting","Wild Jade",["/use Facets of Research"]),
("Enchanting","Sha Crystal",[]),
("Blacksmithing","Lightning Steel Ingot",[]),
("Leatherworking","Magnificence of Leather",[]),
("Leatherworking","Magnificence of Scales",[]),
("Jewelcrafting","Serpent's Heart",["/use Serpent's Heart"]),
]

WOW_ADDITIONAL_COMMAND_DELAY = 3

def getDescription():
    description = "World of Warcraft Login:\n\n"
    description += str(WorldOfWarcraftLogin.charTable())
    description += "\nProfession Cooldown ID's:\n\n"
    for pIdx in range(len(PROFESSION_CDS)):
        (profession,skillname,additionalCommands) = PROFESSION_CDS[pIdx]
        if profession:
            description += str(pIdx) + " - " + profession + ": " + skillname + "\n"
        else:
            description += str(pIdx) + " - " + skillname + "\n"
 #       for cmd in additionalCommands:
 #           description += "   " + cmd + "\n"
    return description


def main():
    BattleNet.setActive()

    parser = argparse.ArgumentParser(description=getDescription(), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('account', metavar='ACCOUNT', type=WorldOfWarcraftLogin.validateAccountId, help='Account ID')
    parser.add_argument('char', metavar='CHAR', type=WorldOfWarcraftLogin.validateCharId, help='Char ID')
    parser.add_argument('professions', metavar='PROFESSION-CD', nargs='+', type=int, choices=range(len(PROFESSION_CDS)), help='Profession Cooldown ID')
    parser.add_argument('--hidden', '-s', dest='hidden', action='store_true', default=False, help='hide online status?')


    args = parser.parse_args()
    accId = args.account
    args = parser.parse_args()

    wow = WorldOfWarcraftLogin(args.account, args.char)
    wow.login(hidden=args.hidden)
    for pIdx in args.professions:
        (profession,skillname,additionalCommands) = PROFESSION_CDS[pIdx]
        if profession:
            wow.craft(profession,skillname)
        for cmd in additionalCommands:
            wow.command(cmd)
            wow.delay("Waiting for " + cmd, WOW_ADDITIONAL_COMMAND_DELAY)
    wow.logout()



if __name__ == "__main__":
    main()