# standard library
import re
import ipaddress

# 3rd party packages
import requests
from rich import print as rprint

# local modules
from util.type import SessionType
from util.crt import CRT


class LRM:
    def __init__(self, url: str, config: dict):
        self.url = url
        self.headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
        self.config = config

    def run(self):
        devices = self.get_lrm()
        sessions = self.get_sessions(devices)
        crt = CRT(self.config, "lrm", sessions)
        crt.run()

    def get_lrm(self):
        """
        Get reservations from LRM using API.
        """
        rprint("Fetching devices from LRM...")
        res = requests.get(
            self.url,
            self.headers,
        )
        devices = res.json()["rows"]
        rprint(f"Loaded [green]{len(devices)}[/green] device(s).")
        return devices

    def get_sessions(self, devices: dict):
        """
        Make session information to deliver in a given form like below.
        sessions = {
            dir_name: [{
                "type": ...,
                "file_name": ...,
                "host": ...,
                "protocol": ...,
                "port": ...,
            },
            {
                "type": ...,
                "file_name": ...,
                "host": ...,
                "protocol": ...,
                "port": ...,
            }, ...]
        }
        """
        sessions = {}

        def add_session(dir_name, session):
            if dir_name in sessions:
                sessions[dir_name].append(session)
            else:
                sessions[dir_name] = [session]

        for device in devices:
            try:
                is_re = "re0_"
                has_re1 = True

                rm_space = device["reservation"]["comment"].replace(" ", "")
                dir_name = re.sub('[\/:*?"<>|]', "_", rm_space)

                if (
                    device["console_re1_ip_address"] == None
                    or device["console_ip_address"] == device["console_re1_ip_address"]
                ):
                    has_re1 = False
                    is_re = ""

                # RE0 SSH
                if device["mgt_ip_address"] != None:
                    re0_ssh = (
                        f"{device['name']}-{is_re}ssh_{device['mgt_ip_address']}.ini"
                    )
                    session = {
                        "type": SessionType.RE0_SSH,
                        "file_name": re0_ssh,
                        "host": device["mgt_ip_address"],
                        "protocol": "SSH2",
                        "port": "22",
                        "jumphost": None,
                    }
                    add_session(dir_name, session)

                # RE0 Console
                if (
                    device["console_ip_address"] != None
                    and len(device["console_ip_address"].split(":")) == 2
                ):
                    re0_con = f"{device['name']}-{is_re}console.ini"
                    re0_console_ip = device["console_ip_address"].split(":")[0]
                    re0_port = device["console_ip_address"].split(":")[1]
                    session = {
                        "type": SessionType.RE0_CON,
                        "file_name": re0_con,
                        "host": re0_console_ip,
                        "protocol": "Telnet",
                        "port": re0_port,
                        "jumphost": None,
                    }
                    add_session(dir_name, session)

                if has_re1 == True:
                    # RE1 SSH
                    # API not provide RE1 ip address. Add 1 to RE0's ip address according to consistency.
                    re1_ip_address = format(
                        ipaddress.ip_address(device["mgt_ip_address"]) + 1
                    )
                    re1_ssh = f"{device['name']}-re1_ssh_{re1_ip_address}.ini"
                    session = {
                        "type": SessionType.RE1_SSH,
                        "file_name": re1_ssh,
                        "host": re1_ip_address,
                        "protocol": "SSH2",
                        "port": "22",
                        "jumphost": None,
                    }
                    add_session(dir_name, session)

                    # RE1 Console
                    re1_con = f"{device['name']}-re1_console.ini"
                    re1_console_ip = device["console_re1_ip_address"].split(":")[0]
                    re1_port = device["console_re1_ip_address"].split(":")[1]
                    session = {
                        "type": SessionType.RE1_CON,
                        "file_name": re1_con,
                        "host": re1_console_ip,
                        "protocol": "Telnet",
                        "port": re1_port,
                        "jumphost": None,
                    }
                    add_session(dir_name, session)
            except Exception:
                rprint(
                    f"[dark_orange][Error] Failed to get a device: {device['name']}[/dark_orange]"
                )
        return sessions
