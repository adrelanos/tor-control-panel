#!/usr/bin/python3 -Bsu

## Copyright (C) 2018 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import json
import os
from subprocess import call
from pathlib import Path

from . import info
from .edit_etc_resolv_conf import edit_etc_resolv_conf_add
from .tor_status import write_to_temp_then_move

whonix = os.path.exists('/usr/share/anon-gw-base-files/gateway')

torrc_file_path = '/usr/local/etc/torrc.d/40_tor_control_panel.conf'
torrc_user_file_path = '/usr/local/etc/torrc.d/50_user.conf'

bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'

command_useBridges = 'UseBridges 1\n'

bridges_command = ['ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n',
                   'ClientTransportPlugin snowflake exec /usr/bin/snowflake-client\n',
                   'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy\n']

bridges_type = ['obfs4',
                'snowflake',
                'meek',
                'Custom bridges']

proxy_torrc = ['HTTPSProxy',
               'Socks4Proxy',
               'Socks5Proxy']

proxies = ['HTTP / HTTPS',
           'SOCKS4',
           'SOCKS5']

proxy_auth = ['HTTPSProxyAuthenticator',
              'Socks5ProxyUsername',
              'Socks5ProxyPassword']


def torrc_path():
    return torrc_file_path

def user_path():
    return torrc_user_file_path

def gen_torrc(args):
    bridge_type = str(args[0]) if len(args) > 0 else 'None'
    print(f"DEBUG bridge_type from gen_torrc : {bridge_type} ")
    custom_bridges = str(args[1]) if len(args) > 1 else 'error-unknown-bridge-type'
    print(f"DEBUG custom_bridges from gen_torrc : {custom_bridges}")
    proxy_type = str(args[2]) if len(args) > 2 else 'None'

    torrc_content = ['%s# %s\n' % (info.torrc_text(), torrc_user_file_path), 'DisableNetwork 0\n']

    if not bridge_type == 'None':
        if bridge_type in bridges_type:
            torrc_content.append(command_useBridges)
            torrc_content.append(bridges_command[bridges_type.index(bridge_type)])
            bridges = json.loads(open(bridges_default_path).read())
            for bridge in bridges['bridges'][bridge_type]:
                if bridge.strip():
                    torrc_content.append('{0}\n'.format(bridge))
    else:
        torrc_content.append('')

    if not custom_bridges == 'None':
        print(f"DEBUG custom bridges / {custom_bridges}")
        bridge = str(custom_bridges.split()[0]) #.lower()
        torrc_content.append('# Custom bridges are used\n')
        torrc_content.append(command_useBridges)
        torrc_content.append(bridges_command[bridges_type.index(bridge)])
        bridge_custom_list = custom_bridges.split('\n')
        for bridge in bridge_custom_list:
            if bridge.strip():
                torrc_content.append('Bridge {0}\n'.format(bridge))
    else:
        torrc_content.append('')

    # Required for meek and snowflake only.
    # https://forums.whonix.org/t/censorship-circumvention-tor-pluggable-transports/2601/9
    if bridge_type.startswith('meek') or bridge_type.startswith('snowflake'):
        edit_etc_resolv_conf_add()

    if proxy_type != 'None' and len(args) >= 7:
        proxy_ip = str(args[3])
        proxy_port = str(args[4])
        proxy_username = str(args[5])
        proxy_password = str(args[6])

        if proxy_type in proxies and proxy_ip and proxy_port:
            torrc_content.append('{0} {1}:{2}\n'.format(proxy_torrc[proxies.index(proxy_type)],
                                                        proxy_ip, proxy_port))
            if proxy_username:
                if proxy_type == proxies[0]:
                    torrc_content.append('{0} {1}:{2}\n'.format(proxy_auth[0], proxy_username,
                                                                proxy_password))
                if proxy_type == proxies[2]:
                    torrc_content.append('{0} {1}\n'.format(proxy_auth[1], proxy_username))
                    if proxy_password:
                        torrc_content.append('{0} {1}\n'.format(proxy_auth[2], proxy_password))
    else:
        torrc_content.append('')

    final_torrc_content = ''.join(torrc_content)
    write_to_temp_then_move(final_torrc_content)

def parse_torrc():
    ## Make sure Torrc exists.
    # command = 'leaprun tor-config-sane'
    # call(command, shell=True)

    # if os.path.exists(torrc_file_path):
    torrc_file_path_obj = Path(torrc_file_path)
    torrc_file_contents = torrc_file_path_obj.read_text(encoding="utf-8")
    torrc_file_lines = torrc_file_contents.split("\n")
    use_bridge = 'UseBridges' in torrc_file_contents
    use_custom_bridges = '# Custom briges are used' in torrc_file_contents
    use_proxy = 'Proxy' in torrc_file_contents

    bridge_type = ''

    if use_bridge:
        for line in torrc_file_lines:
            if line.startswith('#'):
                continue

            if line.startswith('Bridge'):
                line = line.split()
                # The bridge name is 'meek_lite', the bridge type is 'meek'
                if line[1].startswith('meek_lite'):
                    line[1] = 'meek'
                bridge_type = line[1]

            if use_custom_bridges:
                bridge_type = 'Custom bridges'
    else:
        bridge_type = 'None'

    if use_proxy:
        auth_check = False
        proxy_type = proxy_ip = proxy_port = proxy_username = proxy_password = ''
        for line in torrc_file_lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            key, value = parts[0], parts[1]

            if key in proxy_torrc:
                proxy_type = proxies[proxy_torrc.index(key)]
                if ':' in value:
                    ip_port = value.split(':', 1)
                    proxy_ip = ip_port[0]
                    proxy_port = ip_port[1] if len(ip_port) > 1 else ''
                continue

            if key == proxy_auth[0]:  # HTTPSProxyAuthenticator
                auth_check = True
                if ':' in value:
                    user_pass = value.split(':', 1)
                    proxy_username = user_pass[0]
                    proxy_password = user_pass[1] if len(user_pass) > 1 else ''
                continue

            if key == proxy_auth[1]:  # Socks5ProxyUsername
                auth_check = True
                proxy_username = value
                continue

            if key == proxy_auth[2]:  # Socks5ProxyPassword
                auth_check = True
                proxy_password = value
                continue

        if not auth_check:
            proxy_username = ''
            proxy_password = ''

    else:
        proxy_type = 'None'
        proxy_ip = ''
        proxy_port = ''
        proxy_username = ''
        proxy_password = ''

    return (bridge_type, proxy_type, proxy_ip, proxy_port, proxy_username, proxy_password)

    return None
