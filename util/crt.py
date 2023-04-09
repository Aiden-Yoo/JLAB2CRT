# standard library
import os
import shutil

# 3rd party packages
from rich import print as rprint
from Crypto.Hash import SHA256
from Crypto.Cipher import AES


class CRT:
    def __init__(self, config, kind, sessions, is_jh=False):
        self.path = config["crt_path"]
        self.top_dir = config["directory"][kind]["top"]
        self.sub_dir = config["directory"][kind]["sub"]
        self.old_dir = config["directory"][kind]["old"]
        self.jh_dir = config["directory"][kind]["jumphost"] if kind == "vmm" else None
        self.top_path = os.path.join(self.path, self.top_dir)
        self.sub_path = os.path.join(self.top_path, self.sub_dir)
        self.old_path = os.path.join(self.sub_path, self.old_dir)
        self.has_jh = config["vmm"]["jumphost"]["enable"]
        self.is_jh = is_jh
        self.adusername = config["vmm"]["adusername"]
        self.adpassword = config["vmm"]["adpassword"]
        self.username = config[kind]["username"]
        self.password = config[kind]["password"]
        self.sessions = sessions

    def run(self) -> None:
        """
        1. Compare between existing directories and fetched comment.
        2. Move to the old directory if there is no the same comment-named directory. (recognizing it was expired)
        3. Remove all directories in the sub-path except the 'old' directory.
        4. Make directories and sessions.
        """
        exist_dirs = self.get_exist_dirs(self.sub_path)
        self.check_expire_and_move(exist_dirs, self.sessions)
        self.remove_dir()
        self.make_dir()

    def is_exist_or_make(self) -> None:
        """
        Check if directories existing. If not, make directory.
        """
        rprint(f"Checking directories exist for {self.sub_dir}...")

        if os.path.exists(self.path) == False:
            raise Exception("[Error] Default SecureCRT's session directory not found.")

        if os.path.exists(self.top_path) == False:
            os.makedirs(self.top_path)
            rprint(
                f"[dark_orange]'{self.top_dir}'[/dark_orange] directory is created in [green]'{self.path}'[/green]."
            )

        if os.path.exists(self.sub_path) == False:
            os.makedirs(self.sub_path)
            rprint(
                f"[dark_orange]'{self.sub_dir}'[/dark_orange] directory is created in [green]'{self.top_path}'[/green]."
            )

        if os.path.exists(self.old_path) == False:
            os.makedirs(self.old_path)
            rprint(
                f"[dark_orange]'{self.old_dir}'[/dark_orange] directory is created in [green]'{self.sub_path}'[/green]."
            )

        if (
            self.has_jh == True
            and self.jh_dir != None
            and os.path.exists(os.path.join(self.sub_path, self.jh_dir)) == False
        ):
            os.makedirs(os.path.join(self.sub_path, self.jh_dir))
            rprint(
                f"[dark_orange]'jumphost'[/dark_orange] directory is created in [green]'{self.sub_path}'[/green]."
            )

        else:
            rprint("No need to create directorys.")

    def get_exist_dirs(self, target_dir) -> list:
        exist_dirs = []
        with os.scandir(target_dir) as entries:
            for entry in entries:
                if entry.is_dir():
                    exist_dirs.append(entry.name)
        return exist_dirs

    def check_expire_and_move(self, exist, sessions) -> None:
        expired = list(
            set(exist) - set(sessions) - set([self.old_dir]) - set([self.jh_dir])
        )
        if len(expired) != 0:
            rprint(
                f"Found [dark_orange]{len(expired)}[/dark_orange] expired reservation(s). Moving to '{self.old_dir}' directory..."
            )
            for dir in expired:
                expired_dir = os.path.join(self.sub_path, dir)
                to_be = os.path.join(self.old_path, dir)
                if os.path.exists(to_be) == False:
                    shutil.move(expired_dir, self.old_path)
                else:
                    while True:
                        dir = dir + "_dup"
                        to_be = os.path.join(self.old_path, dir)
                        if os.path.exists(to_be) == False:
                            shutil.move(expired_dir, to_be)
                            break
                self.edit_folder_data(self.sub_path)
            print("Done.")
        else:
            print("No expired reservation(s).")

    def edit_folder_data(self, path) -> None:
        """
        Temporary code.
        Sometimes certain directories remain with ini file even though moving to old directory.
        If not resolve with this code, restarting SecureCRT is needed.
        """
        edit_list = ":".join(self.get_exist_dirs(path)) + ":"
        ini = os.path.join(path, "__FolderData__.ini")
        new_content = ""
        with open(ini, "r", encoding="UTF-8") as f:
            lines = f.readlines()
            for line in lines:
                if 'S:"Folder List"=' in line:
                    line = f'S:"Folder List"={edit_list}\n'
                new_content += line
        with open(ini, "w", encoding="UTF-8") as f:
            f.write(new_content)

    def remove_dir(self):
        dirs = self.get_exist_dirs(self.sub_path)
        targets = list(set(dirs) - set([self.old_dir]) - set([self.jh_dir]))
        for target in targets:
            shutil.rmtree(os.path.join(self.sub_path, target))
        self.edit_folder_data(self.sub_path)

    def make_dir(self):
        bundles = self.sessions
        session_num = 0
        for bundle in bundles:
            new_dir_path = os.path.join(self.sub_path, bundle)
            os.mkdir(new_dir_path)
            session_num += self.add_sessions(new_dir_path, bundle)
        rprint(f"[green]All sessions have been created![/green]")
        rprint(f" - Directories: [green]{len(bundles)}[/green]")
        rprint(f" - Sessions: [green]{session_num}[/green]")

    def add_sessions(self, dir_path, bundle_name):
        rprint(f"Creating sessions for {bundle_name}...")
        success = 0
        try:
            for session in self.sessions[bundle_name]:
                new_content = ""
                org_default_ini = os.path.join(self.path, "Default.ini")
                new_default_ini = os.path.join(dir_path, "Default.ini")
                session_ini = os.path.join(dir_path, session["file_name"])
                shutil.copyfile(org_default_ini, new_default_ini)
                shutil.move(new_default_ini, session_ini)
                with open(session_ini, "r", encoding="UTF-8") as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('S:"Hostname"='):
                            line = f'S:"Hostname"={session["host"]}\n'
                        if 'S:"Username"=' in line:
                            if self.is_jh == True:
                                line = f'S:"Username"={self.adusername}\n'
                            else:
                                line = f'S:"Username"={self.username}\n'
                        if line.startswith('S:"Password V2"='):
                            if self.is_jh == True:
                                line = f'S:"Password V2"=02:{self.encrypt_pass(self.adpassword)}\n'
                            else:
                                line = f'S:"Password V2"=02:{self.encrypt_pass(self.password)}\n'
                        if line.startswith('D:"Session Password Saved"='):
                            line = 'D:"Session Password Saved"=00000001\n'
                        if line.startswith('S:"Protocol Name"='):
                            line = f'S:"Protocol Name"={session["protocol"]}\n'
                        if line.startswith('D:"Port"=') or line.startswith(
                            'D:"[SSH2] Port"='
                        ):
                            if session["protocol"] == "SSH2":
                                line = f'D:"[SSH2] Port"={int(session["port"]):08x}\n'
                            else:
                                line = f'D:"Port"={int(session["port"]):08x}\n'
                        if self.has_jh == True and session["jumphost"] != None:
                            if line.startswith('S:"Firewall Name"='):
                                line = f'S:"Firewall Name"=Session:{os.path.join(self.top_dir, self.sub_dir, self.jh_dir, session["jumphost"])}\n'
                        new_content += line
                with open(session_ini, "w", encoding="UTF-8") as f:
                    f.write(new_content)
                rprint(f" - {session['file_name']}")
                success += 1
        except Exception:
            rprint(
                f"[dark_orange][Error] Failed to create {session['file_name']}.[/dark_orange]"
            )
        return success

    def encrypt_pass(self, password):
        iv = b"\x00" * AES.block_size
        key = SHA256.new("".encode("utf-8")).digest()

        plain_bytes = password.encode("utf-8")
        if len(plain_bytes) > 0xFFFFFFFF:
            raise OverflowError("Plaintext is too long.")

        plain_bytes = (
            len(plain_bytes).to_bytes(4, "little")
            + plain_bytes
            + SHA256.new(plain_bytes).digest()
        )
        padded_plain_bytes = plain_bytes + os.urandom(
            AES.block_size - len(plain_bytes) % AES.block_size
        )
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.encrypt(padded_plain_bytes).hex()
