#!/usr/bin/python3 -u

import sys
import os
import json
import shutil
import tempfile
#from anon_connection_wizard import repair_torrc

whonix = os.path.exists('/usr/share/anon-gw-base-files/gateway')
if whonix:
    torrc_file_path = '/usr/local/etc/torrc.d/40_anon_connection_wizard.conf'
    torrc_user_file_path =  '/usr/local/etc/torrc.d/50_user.conf'
else:
    torrc_file_path = '/etc/torrc.d/40_anon_connection_wizard.conf'
    torrc_user_file_path = '/etc/torrc.d/50_user.conf'
torrc_tmp_file_path = ''

bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'

command_useBridges = 'UseBridges 1'
command_use_custom_bridge = '# Custom Bridge is used:'
command_obfs3 = 'ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfs4proxy\n'
command_obfs4 = 'ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n'
command_fte = 'ClientTransportPlugin fte exec /usr/bin/fteproxy --managed\n'
command_scramblesuit = 'ClientTransportPlugin scramblesuit exec /usr/bin/obfs4proxy\n'
command_meek_lite = 'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy\n'
command_meek_amazon_address = 'a0.awsstatic.com\n'
command_meek_azure_address = 'ajax.aspnetcdn.com\n'

bridges_command = ['ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfs4proxy\n',
                   'ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n',
                   'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy\n'
                   'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy\n']

bridges_type = ['obfs3', 'obfs4', 'meek-amazon', 'meek-azure']

#meek_address =    ['a0.awsstatic.com\n',
                   #'ajax.aspnetcdn.com\n']
#requested_meek =  ['meek-amazon', 'meek-azure']


command_http = 'HTTPSProxy '
command_httpAuth = 'HTTPSProxyAuthenticator'
command_sock4 = 'Socks4Proxy '
command_sock5 = 'Socks5Proxy '
command_sock5Username = 'Socks5ProxyUsername'
command_sock5Password = 'Socks5ProxyPassword'

def gen_torrc(args):
    bridge_type =   str(args[0])
    proxy_type =    str(args[1])
    if not proxy_type == 'None':
        proxy_ip =          str(args[2])
        proxy_port =        str(args[3])
        proxy_username =    str(args[4])
        proxy_password  =   str(args[5])

    #repair_torrc.repair_torrc()  # This guarantees a good set of torrc files

    # Creates a file and returns a tuple containing both the handle and the path.
    # we are responsible for removing tmp file when finished which is the reason we
    # use shutil.move(), not shutil.copy(), below
    handle, torrc_tmp_file_path = tempfile.mkstemp()

    # Write directly to torrc. If we create a tempfile and move it to torrc.d,
    # tor daemon cannot open it: 'permission denied'.
    with open(torrc_file_path, "w") as f:
        f.write("\
# This file is generated by and should ONLY be used by anon-connection-wizard.\n\
# User configuration should go to " + torrc_user_file_path + ", not here. Because:\n\
#    1. This file can be easily overwritten by anon-connection-wizard.\n\
#    2. Even a single character change in this file may cause error.\n\
# However, deleting this file will be fine since a new plain file will be generated \
the next time you run anon-connection-wizard.\n\
")

        if bridge_type == 'None':
            f.write('DisableNetwork 0\n')
        else:
            f.write(command_useBridges + '\n')
            #if bridge_type in bridges_type:
                #command = bridges_command[bridges_type.index(bridge_type)]
                #f.write(command)
            if bridge_type == 'obfs3':
                f.write(command_obfs3)
            elif bridge_type == 'scramblesuit':
                f.write(command_scramblesuit)
            elif bridge_type == 'obfs4':
                f.write(command_obfs4)
            elif bridge_type == 'meek-amazon':
                f.write(command_meek_lite)
            elif bridge_type == 'meek-azure':
                f.write(command_meek_lite)
            bridges = json.loads(open(bridges_default_path).read())
            # The bridges variable are like a multilayer-dictionary
            for bridge in bridges['bridges'][bridge_type]:
                f.write('bridge {0}\n'.format(bridge))
            f.write('DisableNetwork 0\n')
            #else:  # Use custom bridges
                #f.write(command_use_custom_bridge + '\n')  # mark custom bridges are used

                #if bridge_custom.lower().startswith('obfs4'):
                    #f.write(command_obfs4 + '\n')
                #elif bridge_custom.lower().startswith('obfs3'):
                    #f.write(command_obfs3 + '\n')
                #elif bridge_custom.lower().startswith('fte'):
                    #f.write(command_fte + '\n')
                #elif bridge_custom.lower().startswith('meek_lite'):
                    #f.write(command_meek_lite + '\n')

                ## Write the specific bridge address, port, cert etc.
                #bridge_custom_list = bridge_custom.split('\n')
                #for bridge in bridge_custom_list:
                    #if bridge != '':  # check if the line is actually empty
                        #f.write('bridge {0}\n'.format(bridge))

    #''' The part is the IO to torrc for proxy settings.
    #Related official docs: https://www.torproject.org/docs/tor-manual.html.en
    #'''
    #if use_proxy:
        #with open(torrc_tmp_file_path, 'a') as f:
        if proxy_type == 'HTTP/HTTPS':
            f.write('HTTPSProxy {0}:{1}\n'.format(proxy_ip, proxy_port))
            if (proxy_username != ''):  # there is no need to check password because
                                                #username is essential
                f.write('HTTPSProxyAuthenticator {0}:{1}\n'.format(proxy_username, proxy_password))
        elif proxy_type == 'SOCKS4':
            # Notice that SOCKS4 does not support proxy username and password
            f.write('Socks4Proxy {0}:{1}\n'.format(proxy_ip, proxy_port))
        elif proxy_type == 'SOCKS5':
            f.write('Socks5Proxy {0}:{1}\n'.format(proxy_ip, proxy_port))
            if (proxy_username != ''):
                f.write('Socks5ProxyUsername {0}\n'.format(proxy_username))
                f.write('Socks5ProxyPassword {0}\n'.format(proxy_password))

    #shutil.move(torrc_tmp_file_path, torrc_file_path)

def parse_torrc():
    if os.path.exists(torrc_file_path):
        use_bridge = False
        use_proxy = False
        if 'UseBridges' in open(torrc_file_path).read():
            use_bridge = True
        if 'Proxy' in open(torrc_file_path).read():
            use_proxy = True

        if use_bridge:
            with open(torrc_file_path, 'r') as f:
                for line in f:
                    if 'ClientTransportPlugin' in line:
                        bridge_type = line.split()[1]
        else:
            bridge_type = 'None'

        if use_proxy:
            with open(torrc_file_path, 'r') as f:
                for line in f:
                    if 'Proxy' in line:
                        proxy_type = line.split()[0]
                        proxy_socket = line.split()[1]
        else:
            proxy_type = 'None'
            proxy_socket = 'None'

        return(bridge_type, proxy_type, proxy_socket)
