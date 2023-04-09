#!/usr/bin/env python
# -*-coding:utf-8 -*-
"""
@File    :   lab2crt.py
@Time    :   2023/04/09 03:36:36
@Author  :   Aiden Yoo
@Version :   2.0.0
@Contact :   you1367@gmail.com
@Desc    :   None
"""


# standard library
import sys
import platform
import getpass

# 3rd party packages
import yaml

# local modules
from util.lrm import LRM
from util.crt import CRT
from util.vmm import VMM


OS = platform.system()
USER_NAME = getpass.getuser()
# URL has been removed
LRM_URL = f"https://[[REMOVED]]?reserved_by={USER_NAME}&_flat"


def default_session_path() -> str:
    if OS == "Windows":
        SESSION_PATH = f"C:\Documents and Settings\{USER_NAME}\Application Data\VanDyke\Config\Sessions"
    elif OS == "Darwin":
        SESSION_PATH = f"/Users/{USER_NAME}/Library/Application Support/VanDyke/SecureCRT/Config/Sessions"
    else:
        raise Exception("[Error] Unsupported operating system.")
    return SESSION_PATH


def get_config() -> tuple:
    with open("config.yml", "r", encoding="UTF-8") as f:
        config = yaml.safe_load(f)
        if config["crt_path"] == None:
            config["crt_path"] = default_session_path()
        if config["vmm"]["adusername"] == None:
            config["vmm"]["adusername"] = getpass.getuser()
        if config["vmm"]["adpassword"] == None:
            config["vmm"]["adpassword"] = getpass.getpass(
                prompt="###################################\n#    Please input AD password     # \n###################################\n - Password: ",
                stream=None,
            )
        if config["vmm"]["labpassword"] == None:
            config["vmm"]["labpassword"] = getpass.getpass(
                prompt="###################################\n#  Please input JNPRLAB password  # \n###################################\n - Password: ",
                stream=None,
            )
        return config


def check_dir(config, kind):
    CRT(
        config,
        kind,
        {},
    ).is_exist_or_make()


def help():
    print("Usage:")
    print("    python ./lab2crt.py [-a | -k <lrm|vmm>]")
    print("")
    print("    [-a]                   Create sessions from all kinds of lab(LRM/VMM).")
    print("                           This parameter applied by default.")
    print("")
    print("    [-k <lrm|vmm>]         Create sessions selectively between LRM and VMM")
    print("                           This parameter is optional.")
    print("")


if __name__ == "__main__":
    argc = len(sys.argv)
    argv = sys.argv

    config = get_config()

    if argc == 1 or (argc == 2 and argv[1].lower() == "-a"):
        check_dir(config, "lrm")
        lrm = LRM(LRM_URL, config)
        lrm.run()
        check_dir(config, "vmm")
        vmm = VMM(config)
        vmm.run()
        pass
    elif argc == 3:
        if argv[2].lower() == "lrm":
            check_dir(config, "lrm")
            lrm = LRM(LRM_URL, config)
            lrm.run()
        elif argv[2].lower() == "vmm":
            check_dir(config, "vmm")
            vmm = VMM(config)
            vmm.run()
        else:
            help()
    else:
        help()
