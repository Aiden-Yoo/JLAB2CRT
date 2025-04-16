# JLAB2CRT

JLAB2CRT is a script that makes SecureCRT sessions automatically for UltraLAB & VMM users.
It fetches UltraLAB information by using LRM(LAB Resource Management) Core API.
It was made by adding LRM2CRT's feature. This addition makes automating VMM session creation.

## Note

This repository is for recording my work. This is for use in Juniper Networks' internal system, and important information has been deleted and modified to remain public repo. Therefore, this source code cannot be guaranteed to operate in any environment.

<!-- GETTING STARTED -->

## Getting Started

### Prerequisites

- Windows or Mac
- Python 3.7+
- SecureCRT

### Installation

_Python 3.7+ is required to use jlab2crt. If it is not installed on user environment, need to install python by referring to the official document. ([for Windows](https://docs.python.org/3/using/windows.html), [for Mac](https://docs.python.org/3/using/mac.html#))_

1. Clone the repo

   ```sh
   git clone https://github.com/Aiden-Yoo/JLAB2CRT.git
   ```

   or download manually.

2. Move directory
   ```sh
   cd jlab2crt
   ```
3. Install python packages
   ```sh
   pip install -r ./requirements.txt
   ```

<!-- USAGE EXAMPLES -->

## Usage

1. Move directory

   ```sh
   cd jlab2crt
   ```

2. Edit file from `config.yml.sample` to `config.yml`
   ```yaml
   ---
   crt_path:
   directory:
     top: JNPR
     sub: UltraLab
     old: old
     ...
   ```
   Put in `crt_path` if changed default SecureCRT data path - Refer to the config.yml.sample. Please refer to the `config.yml` to get more details.
3. Execute `jlab2crt.py`

   - Create sessions All of LAB system(UltraLAB, VMM).

   ```sh
   python ./jlab2crt.py
   or
   python ./jlab2crt.py -a
   ```

   - Create sessions for `UltraLAB` only.

   ```sh
   python ./jlab2crt.py -k lrm
   ```

   - Create sessions for `VMM` only.

   ```sh
   python ./jlab2crt.py -k vmm
   ```

4. Check created sessions in the SecureCRT

   The sessions and directories will be created according to the name that configured in the config.yml like the below. The session directories' name refers to the comments on the reservation.

   ```sh
    └JNPR
      ├UltraLab
      │ ├old
      │ ├Session directory 1
      │ ├Session directory 2
      │ ├Session directory 3
      │ └...
      └VMM
        ├old
        ├Session directory 1
        ├Session directory 2
        ├Session directory 3
        └...
   ```

<!-- TODO -->

<!-- ## To-do -->

<!-- CONTACT -->

## Contact

Aiden Yoo - you1367@gmail.com

Project Link: [https://github.com/Aiden-Yoo/LAB2CRT](https://github.com/Aiden-Yoo/JLAB2CRT)

<p align="right">(<a href="#jlab2crt">back to top</a>)</p>
