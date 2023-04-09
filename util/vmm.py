# standard library
import os
import getpass

# 3rd party packages
import asyncssh
import asyncio
from rich import print as rprint

# local modules
from util.type import SessionType
from util.crt import CRT


class VMM:
    def __init__(self, config: dict):
        self.config = config
        self.path = config["crt_path"]
        self.top_dir = config["directory"]["vmm"]["top"]
        self.sub_dir = config["directory"]["vmm"]["sub"]
        self.old_dir = config["directory"]["vmm"]["old"]
        self.jh_dir = config["directory"]["vmm"]["jumphost"]
        self.pod_list = config["vmm"]["pod"]["hosts"]
        self.use_jh = config["vmm"]["jumphost"]["enable"]
        self.jh_list = config["vmm"]["jumphost"]["hosts"]
        self.adpassword = config["vmm"]["adpassword"]
        self.labpassword = config["vmm"]["labpassword"]
        self.exclude_kwd = [
            exclude_kwd.lower() for exclude_kwd in config["vmm"]["keyword"]["exclude"]
        ]
        self.username = getpass.getuser()
        self.jh = None
        self.pod = None

    def run(self) -> None:
        if self.use_jh == True:
            session = {}
            self.get_server(SessionType.JUMPHOST)
            jh_session = {
                "type": SessionType.JUMPHOST,
                "file_name": self.jh + ".ini",
                "host": self.jh,
                "protocol": "SSH2",
                "port": "22",
                "jumphost": None,
            }
            session[self.jh_dir] = [jh_session]
            CRT(self.config, "vmm", session, True).add_sessions(
                os.path.join(self.path, self.top_dir, self.sub_dir, self.jh_dir),
                self.jh_dir,
            )
            self.get_server(SessionType.VMM_JH)
            pods = self.get_pod(SessionType.VMM_JH)
            sessions = self.get_sessions(SessionType.VMM_JH, pods)
            crt = CRT(self.config, "vmm", sessions, False)
        if self.use_jh == False:
            self.get_server(SessionType.VMM)
            pods = self.get_pod(SessionType.VMM)
            sessions = self.get_sessions(SessionType.VMM, pods)
            crt = CRT(self.config, "vmm", sessions, False)
        crt.run()

    def get_server(self, session_type):
        async def conn_svr(server):
            # jumphost or vmm w/o jumphost
            if session_type.value == 0 or session_type.value == 6:
                conn = await asyncio.wait_for(
                    asyncssh.connect(
                        server,
                        port=22,
                        username=self.username,
                        password=self.adpassword
                        if session_type.value == 0
                        else self.labpassword,
                        client_keys=None,
                        known_hosts=None,
                    ),
                    timeout=4,
                )
                async with conn:
                    start_time = loop.time()
                    await conn.run('echo "test"')
                    end_time = loop.time()
                return conn, end_time - start_time
            # vmm w/ jumphost
            if session_type.value == 5:
                async with asyncssh.connect(
                    self.jh,
                    port=22,
                    username=self.username,
                    password=self.adpassword,
                    client_keys=None,
                    known_hosts=None,
                ) as tunnel:
                    conn = await asyncio.wait_for(
                        asyncssh.connect(
                            server,
                            port=22,
                            username=self.username,
                            password=self.labpassword,
                            client_keys=None,
                            known_hosts=None,
                            tunnel=tunnel,
                        ),
                        timeout=4,
                    )
                    async with conn:
                        start_time = loop.time()
                        await conn.run('echo "test"')
                        end_time = loop.time()
                    return conn, end_time - start_time

        async def get_ssh_time(server):
            try:
                conn, time = await conn_svr(server)
                return time
            except asyncssh.Error as e:
                if "Host key verification failed" in str(e):
                    hostkeys = asyncssh.HostKeys()
                    hostkeys.add(server, "ssh-rsa", conn.get_server_host_key())
                    asyncssh.write_host_key(
                        os.path.expanduser("~/.ssh/known_hosts"), hostkeys
                    )
                    _, time = await conn_svr(server)
                    return time
                else:
                    return float("inf")
            except (OSError, asyncio.exceptions.TimeoutError):
                return float("inf")

        async def find_fastest_server(servers):
            tasks = [get_ssh_time(server) for server in servers]
            results = await asyncio.gather(*tasks)
            # print(results)
            return servers[results.index(min(results))]

        print(f"Finding the fastest {session_type.name.lower()}...")
        if session_type.value == 0:
            server_list = self.jh_list

        if session_type.value == 5 or session_type.value == 6:
            server_list = self.pod_list

        loop = asyncio.get_event_loop()
        fastest_server = loop.run_until_complete(find_fastest_server(server_list))
        rprint(
            f"The fastest server is [green]{fastest_server}[/green]. Choose this server."
        )
        if session_type.value == 0:
            self.jh = fastest_server
        if session_type.value == 5 or session_type.value == 6:
            self.pod = fastest_server

    def get_pod(self, session_type):
        pods = {}

        async def conn_svr(server):
            try:
                # jumphost or vmm w/o jumphost
                if session_type.value == 6:
                    conn = await asyncio.wait_for(
                        asyncssh.connect(
                            server,
                            port=22,
                            username=self.username,
                            password=self.labpassword,
                            client_keys=None,
                            known_hosts=None,
                        ),
                        timeout=4,
                    )
                    async with conn:
                        for pod in self.pod_list:
                            result = await conn.run(
                                f"cat ~/.vmmgr/{pod}.config.db | grep 'Config-file'"
                            )
                            if len(result.stdout) != 0:
                                pod_name = pod.split(".")[0]
                                dir_name = result.stdout.split("/")[-3]
                                pods[pod_name] = dir_name
                # vmm w/ jumphost
                if session_type.value == 5:
                    async with asyncssh.connect(
                        self.jh,
                        port=22,
                        username=self.username,
                        password=self.adpassword,
                        client_keys=None,
                        known_hosts=None,
                    ) as tunnel:
                        conn = await asyncio.wait_for(
                            asyncssh.connect(
                                server,
                                port=22,
                                username=self.username,
                                password=self.labpassword,
                                client_keys=None,
                                known_hosts=None,
                                tunnel=tunnel,
                            ),
                            timeout=4,
                        )
                        async with conn:
                            for pod in self.pod_list:
                                result = await conn.run(
                                    f"cat ~/.vmmgr/{pod}.config.db | grep 'Config-file'"
                                )
                                if len(result.stdout) != 0:
                                    pod_name = pod.split(".")[0]
                                    dir_name = result.stdout.split("/")[-3]
                                    pods[pod_name] = dir_name
                # print(pods)
            except asyncssh.Error as e:
                if "Host key verification failed" in str(e):
                    hostkeys = asyncssh.HostKeys()
                    hostkeys.add(server, "ssh-rsa", conn.get_server_host_key())
                    asyncssh.write_host_key(
                        os.path.expanduser("~/.ssh/known_hosts"), hostkeys
                    )
                    await conn_svr(server)
                else:
                    return float("inf")
            except (OSError, asyncio.exceptions.TimeoutError):
                return float("inf")

        loop = asyncio.get_event_loop()
        task = conn_svr(self.pod)
        loop.run_until_complete(asyncio.gather(task))
        return pods

    def get_sessions(self, session_type, pods):
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

        async def conn_svr(server):
            try:
                # jumphost or vmm w/o jumphost
                if session_type.value == 6:
                    conn = await asyncio.wait_for(
                        asyncssh.connect(
                            server,
                            port=22,
                            username=self.username,
                            password=self.adpassword
                            if session_type.value == 0
                            else self.labpassword,
                            client_keys=None,
                            known_hosts=None,
                        ),
                        timeout=4,
                    )
                    async with conn:
                        result = await conn.run(f"vmm ip")
                        if len(result.stdout) != 0:
                            lines = result.stdout.strip("\n").splitlines()
                            for line in lines:
                                include = False
                                for keyword in self.exclude_kwd:
                                    if keyword in line.lower():
                                        include = True
                                        break
                                if not include:
                                    split_line = line.split()
                                    session = {
                                        "type": session_type,
                                        "file_name": "_".join(split_line) + ".ini",
                                        "host": split_line[1],
                                        "protocol": "SSH2",
                                        "port": "22",
                                        "jumphost": self.jh,
                                    }
                                    add_session(f"{server}_{pods[server]}", session)
                # vmm w/ jumphost
                if session_type.value == 5:
                    async with asyncssh.connect(
                        self.jh,
                        port=22,
                        username=self.username,
                        password=self.adpassword,
                        client_keys=None,
                        known_hosts=None,
                    ) as tunnel:
                        conn = await asyncio.wait_for(
                            asyncssh.connect(
                                server,
                                port=22,
                                username=self.username,
                                password=self.labpassword,
                                client_keys=None,
                                known_hosts=None,
                                tunnel=tunnel,
                            ),
                            timeout=4,
                        )
                        async with conn:
                            result = await conn.run(f"vmm ip")
                            if len(result.stdout) != 0:
                                lines = result.stdout.strip("\n").splitlines()
                                for line in lines:
                                    include = False
                                    for keyword in self.exclude_kwd:
                                        if keyword in line.lower():
                                            include = True
                                            break
                                    if not include:
                                        split_line = line.split()
                                        session = {
                                            "type": session_type,
                                            "file_name": "_".join(split_line) + ".ini",
                                            "host": split_line[1],
                                            "protocol": "SSH2",
                                            "port": "22",
                                            "jumphost": self.jh,
                                        }
                                        add_session(f"{server}_{pods[server]}", session)
            except asyncssh.Error as e:
                if "Host key verification failed" in str(e):
                    hostkeys = asyncssh.HostKeys()
                    hostkeys.add(server, "ssh-rsa", conn.get_server_host_key())
                    asyncssh.write_host_key(
                        os.path.expanduser("~/.ssh/known_hosts"), hostkeys
                    )
                    await conn_svr(server)
                else:
                    return float("inf")
            except (OSError, asyncio.exceptions.TimeoutError):
                return float("inf")

        print(f"Gathering target sessions from each pods...")
        loop = asyncio.get_event_loop()
        tasks = [conn_svr(pod) for pod in pods]
        loop.run_until_complete(asyncio.gather(*tasks))
        return sessions
