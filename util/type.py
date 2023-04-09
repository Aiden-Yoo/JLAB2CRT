from enum import Enum


class SessionType(Enum):
    JUMPHOST = 0
    RE0_SSH = 1
    RE0_CON = 2
    RE1_SSH = 3
    RE1_CON = 4
    VMM_JH = 5
    VMM = 6
