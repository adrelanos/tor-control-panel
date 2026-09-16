#!/usr/bin/python3 -Bsu

## Copyright (C) 2018 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import os
import signal
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QCursor, QTextCursor
from guimessages.translations import _translations

from . import tor_status, repair_torrc, tor_bootstrap, torrc_gen, info
from .tor_status import cat, write_to_temp_then_move


def signal_handler(sig, frame):
    sys.exit(128 + sig)


class Common:
    translations_path = '/usr/share/anon-connection-wizard/translations.yaml'

    dummy = ''

    torrc_file_path = torrc_gen.torrc_path()
    torrc_user_file_path = torrc_gen.user_path()
    acw_comm_file_path = '/run/anon-connection-wizard/tor.conf'

    bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'

    default_bridges = ['obfs4',
                       'snowflake',
                       'meek']

    bridges = torrc_gen.bridges_type

    custom_bridges_accept: bool = False

    use_default_bridges = False
    bridge_type = 'obfs4'
    use_custom_bridges = False
    custom_bridges = ""
    use_proxy: bool = False
    proxy_type = 'HTTP / HTTPS'
    proxy_ip = ''
    proxy_port = ''
    proxy_username = ''
    proxy_password = ''

    init_tor_status = ''
    disable_tor = False

    font_title = QtGui.QFont()
    font_title.setPointSize(13)
    font_title.setBold(True)
    font_title.setWeight(95)

    font_description_main = QtGui.QFont()
    font_description_main.setPointSize(11)
    font_description_main.setBold(True)
    font_description_main.setWeight(85)

    font_description_minor = QtGui.QFont()
    font_description_minor.setPointSize(10)
    font_description_minor.setBold(False)
    font_description_minor.setWeight(30)

    font_option = QtGui.QFont()
    font_option.setPointSize(11)
    font_option.setBold(True)
    font_option.setWeight(65)

    wizard_steps = ['connection_main_page',
                    'bridge_wizard_page',
                    'proxy_wizard_page',
                    'torrc_page',
                    'tor_status_page']


class ConnectionMainPage(QWizardPage):
    def __init__(self):
        super(ConnectionMainPage, self).__init__(None)

        self.steps = Common.wizard_steps

        self.page_layout = QVBoxLayout(self)
        self.label_1 = QLabel()
        self.page_layout.addWidget(self.label_1)
        self.label_2 = QLabel()
        self.page_layout.addWidget(self.label_2)
        self.label_3 = QLabel()
        self.page_layout.addWidget(self.label_3)
        self.connect_option = QRadioButton()
        self.page_layout.addWidget(self.connect_option)
        self.label_4 = QLabel()
        self.page_layout.addWidget(self.label_4)
        self.configure_option = QRadioButton()
        self.page_layout.addWidget(self.configure_option)
        self.label_5 = QLabel()
        self.page_layout.addWidget(self.label_5)
        self.disable_option = QRadioButton()
        self.page_layout.addWidget(self.disable_option)

        self.setLayout(self.page_layout)

        self.setup_ui()

    def setup_ui(self):
        font_description_main = Common.font_description_main
        font_option = Common.font_option

        self.label_1.setWordWrap(True)
        self.label_1.setText('''
<br>Before you connect to the Tor network, you need to provide information about this computer's
Internet connection.''')


        self.label_2.setFont(font_description_main)
        self.label_2.setText('Which of the following best describes your situation?<br>')

        self.label_3.setWordWrap(True)
        self.label_3.setText(
            'I would like to connect directly to the Tor network. This will work in most situations.')

        self.connect_option.setFont(font_option)
        self.connect_option.setText('Connect')
        self.connect_option.setChecked(True)
        self.configure_option.setFont(font_option)
        self.configure_option.setText('Configure')
        self.disable_option.setFont(font_option)
        self.disable_option.setText('Disable Tor')
        self.disable_option.show()

        self.label_4.setWordWrap(True)
        self.label_4.setText(
            '''<br>This computer's Internet connection is censored or proxied.<br>
I need to configure bridges or proxy settings.''')

        self.label_5.setWordWrap(True)
        self.label_5.setText(
            '''<br>I do not want to connect automatically to the Tor network.<br>
Choosing this option will prevent browsing or any Internet-related activity.<br>
See next page for more details.''')
        self.label_5.show()

    def nextId(self):
        if self.connect_option.isChecked():
            # clear all setting
            Common.disable_tor = False
            Common.use_default_bridges = False
            Common.use_custom_bridges = False
            Common.use_proxy = False
            return self.steps.index('torrc_page')

        elif self.configure_option.isChecked():
            Common.disable_tor = False
            return self.steps.index('bridge_wizard_page')

        elif self.disable_option.isChecked():
            Common.disable_tor = True
            return self.steps.index('tor_status_page')

        return None


class BridgesWizardPage(QWizardPage):
    def __init__(self):
        super(BridgesWizardPage, self).__init__(None)

        self.steps = Common.wizard_steps
        self.bridges = Common.bridges

        self.valid_custom_bridges = QMessageBox(QMessageBox.Warning, 'Warning',
                                                    info.invalid_custom_bridges(), QMessageBox.Ok)

        self.title_frame = QFrame()
        self.title_layout = QGridLayout(self.title_frame)
        self.title_label = QLabel()
        self.title_layout.addWidget(self.title_label, 1, 0, Qt.AlignmentFlag.AlignCenter)
        self.title_frame.setMaximumHeight(100)

        self.header_frame = QFrame()
        self.header_frame.setMaximumHeight(150)
        self.header_layout = QGridLayout(self.header_frame)
        self.bridges_checkbox = QCheckBox()
        self.bridges_checkbox.setMaximumHeight(20)
        self.show_help_censorship = QPushButton()
        self.header_layout.addWidget(self.bridges_checkbox, 1, 0, Qt.AlignmentFlag.AlignLeft)
        self.header_layout.addWidget(self.show_help_censorship, 1, 1 ,Qt.AlignmentFlag.AlignRight)

        self.bridges_frame = QFrame()
        self.bridges_layout = QHBoxLayout(self.bridges_frame)
        self.bridges_label = QLabel(self.bridges_frame)
        self.bridges_combo = QComboBox(self.bridges_frame)
        self.bridges_combo.setMaximumHeight(24)
        self.bridges_combo.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        self.bridges_layout.addWidget(self.bridges_label)
        self.bridges_layout.addWidget(self.bridges_combo, Qt.AlignmentFlag.AlignLeft)

        self.custom_frame = QFrame()
        self.custom_frame.setMinimumSize(425, 520)
        self.custom_layout = QGridLayout(self.custom_frame)
        self.custom_label = QLabel(self.custom_frame)
        self.custom_label.setMinimumHeight(24)
        self.custom_bridges_help = QPushButton(self.custom_frame)
        self.custom_bridges_help.setMinimumSize(120, 24)
        self.h_spacer = QSpacerItem(40, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.custom_bridges = QtWidgets.QTextEdit(self.custom_frame)
        self.custom_bridges.setMinimumSize(440, 480)

        self.custom_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.custom_layout.addWidget(self.custom_label, 1, 0)

        self.custom_bridges_help.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.custom_layout.addWidget(self.custom_bridges_help, 1, 1, Qt.AlignmentFlag.AlignRight)

        self.custom_layout.addItem(self.h_spacer, 2, 0)

        self.custom_bridges.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.custom_layout.addWidget(self.custom_bridges, 3, 0)

        self.dummy_frame = QFrame()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title_frame)
        self.layout.addWidget(self.header_frame)
        self.layout.addWidget(self.bridges_frame)
        self.layout.addWidget(self.custom_frame)
        self.layout.addWidget(self.dummy_frame)
        self.setLayout(self.layout)

        self.setup_ui()

    def setup_ui(self):
        for bridge in self.bridges:
            self.bridges_combo.addItem(bridge)

        font_title = Common.font_title
        font_description_main = Common.font_description_main

        self.bridges_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.custom_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.bridges_frame.show()
        self.custom_frame.hide()

        self.title_label.setText('Tor Bridges Configuration')
        self.title_label.setFont(font_title)

        if self.bridges_checkbox.isChecked():
            self.show_bridges_panel()
        self.bridges_checkbox.toggled.connect(self.show_bridges_panel)

        self.bridges_checkbox.setText("I need bridges to bypass censorship.")
        self.bridges_checkbox.setFont(font_description_main)

        self.bridges_combo.currentIndexChanged.connect(self.set_bridges_panel)

        self.show_help_censorship.setEnabled(True)
        self.show_help_censorship.setText('&Help ?')
        self.show_help_censorship.setMaximumWidth(75)
        self.show_help_censorship.clicked.connect(info.show_help_censorship)

        self.bridges_label.setText('Select a bridge type:')

        self.custom_label.setFont(Common.font_description_minor)
        self.custom_label.setText('Enter at least 2 bridge relays (one per line).')

        self.custom_bridges_help.setText('&How to get Bridges?')
        self.custom_bridges_help.clicked.connect(info.custom_bridges_help)

        self.custom_bridges.setLineWrapMode(QTextEdit.NoWrap)

    def show_bridges_panel(self):
        if self.bridges_checkbox.isChecked():
            index = self.bridges_combo.findText(Common.bridge_type)
            self.bridges_combo.setCurrentIndex(index)
            self.bridges_frame.show()

            if Common.use_default_bridges:
                self.bridges_label.setEnabled(True)
                self.bridges_combo.setEnabled(True)
                self.custom_frame.hide()

            elif Common.use_custom_bridges:
                self.custom_frame.show()

        else:
            Common.bridge_type = 'None'
            Common.use_default_bridges = False
            Common.use_custom_bridges = False
            self.bridges_frame.hide()
            self.custom_frame.hide()

    def set_bridges_panel(self):
        if self.bridges_checkbox.isChecked():
            Common.bridge_type = self.bridges_combo.currentText()
            Common.use_custom_bridges = Common.bridge_type == 'Custom bridges'
            Common.use_default_bridges = Common.bridge_type in Common.default_bridges

            if Common.use_custom_bridges:
                self.custom_frame.show()

            elif Common.use_default_bridges:
                self.custom_frame.hide()

            if Common.use_default_bridges:
                Common.bridge_type = self.bridges_combo.currentText()

    def check_valid_custom_bridges(self):
        bridges = Common.custom_bridges
        return (bridges.startswith('obfs4')
                or (('.' in bridges) and (':' in bridges)))

    def nextId(self):
        if not Common.use_custom_bridges:
            return self.steps.index('proxy_wizard_page')

        if Common.use_custom_bridges:
            if not self.custom_bridges.toPlainText() == "":
                Common.bridge_type = self.bridges_combo.currentText()
                Common.custom_bridges = self.custom_bridges.toPlainText()

            if not self.check_valid_custom_bridges():
                self.valid_custom_bridges.setWindowModality(Qt.WindowModal)
                self.valid_custom_bridges.exec_()
                return self.steps.index('bridge_wizard_page')
            else:
                return self.steps.index('proxy_wizard_page')


class ProxyWizardPage(QWizardPage):
    def __init__(self):
        super(ProxyWizardPage, self).__init__(None)

        self.steps = Common.wizard_steps

        self.proxies = ['None',
                        'HTTP / HTTPS',
                        'SOCKS4',
                        'SOCKS5']

        self.proxy_type = 'None'

        self.valid_proxy = QMessageBox(QMessageBox.Warning, 'Warning',
                                    info.invalid_ip_port(), QMessageBox.Ok)

        self.header_frame = QFrame()
        self.header_layout = QGridLayout(self.header_frame)
        self.title_label = QLabel()
        self.proxy_checkbox = QCheckBox()
        self.header_layout.addWidget(self.title_label, 1, 0)
        self.header_layout.addWidget(self.proxy_checkbox, 2, 0)

        self.proxy_frame = QFrame()
        self.proxy_layout = QGridLayout(self.proxy_frame)

        self.label = QLabel()
        self.proxy_help = QPushButton()
        self.proxytype_label = QLabel()
        self.proxy_combo = QComboBox()
        self.spacer = QSpacerItem(0, 100, QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.ip_label = QLabel()
        self.ip_edit = QLineEdit()
        self.port_label = QLabel()
        self.port_edit = QLineEdit()
        self.user_label = QLabel()
        self.user_edit = QLineEdit()
        self.password_label = QLabel()
        self.password_edit = QLineEdit()

        self.proxy_help_layout = QGridLayout()
        self.proxy_help_layout.addWidget(self.label, 1, 0)
        self.proxy_help_layout.addWidget(self.proxy_help, 1, 3)
        self.proxy_layout.addLayout(self.proxy_help_layout, 1, 0)

        self.proxy_type_layout = QHBoxLayout()
        self.proxy_type_layout.addWidget(self.proxytype_label)
        self.proxy_type_layout.addWidget(self.proxy_combo, 1, Qt.AlignmentFlag.AlignLeft)
        self.proxy_type_layout.addItem(self.spacer)
        self.proxy_layout.addLayout(self.proxy_type_layout, 2, 0)

        self.proxy_args_layout = QGridLayout()
        self.proxy_args_layout.addWidget(self.ip_label, 1, 0)
        self.proxy_args_layout.addWidget(self.ip_edit, 1, 1)
        self.proxy_args_layout.addWidget(self.port_label, 1, 2)
        self.proxy_args_layout.addWidget(self.port_edit, 1, 3)
        self.proxy_layout.addLayout(self.proxy_args_layout, 3, 0)

        self.user_layout = QGridLayout()
        self.user_layout.addWidget(self.user_label, 1, 0)
        self.user_layout.addWidget(self.user_edit, 1, 1)
        self.user_layout.addWidget(self.password_label, 1, 2)
        self.user_layout.addWidget(self.password_edit, 1, 3)
        self.proxy_layout.addLayout(self.user_layout, 4, 0)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.header_frame)
        self.layout.addWidget(self.proxy_frame)
        self.setLayout(self.layout)

        self.setup_ui()

    def setup_ui(self):
        font_title = Common.font_title
        font_description_main = Common.font_description_main

        self.header_frame.setMaximumHeight(200)

        self.proxy_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)

        self.title_label.setText('Proxy Configuration<br>')
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setFont(font_title)

        self.proxy_checkbox.setText("Use proxy before connecting to the Tor network")
        self.proxy_checkbox.setFont(font_description_main)

        self.proxy_frame.hide()
        self.proxy_checkbox.toggled.connect(self.show_proxy_frame)
        self.label.setText("Enter the proxy settings.")

        self.proxy_help.setText('Help ?')
        self.proxy_help.setMaximumWidth(75)
        self.proxy_help.clicked.connect(info.show_proxy_help)

        self.proxytype_label.setText("Proxy type: ")

        for proxy in self.proxies:
            self.proxy_combo.addItem(proxy)

        self.proxy_combo.currentIndexChanged.connect(self.proxy_option_changed)

        self.ip_label.setText("Address:   ")
        self.ip_edit.setPlaceholderText('Example: 127.0.0.1')
        self.ip_edit.setText(Common.proxy_ip)

        self.port_label.setText("    Port: ")
        self.port_edit.setPlaceholderText('1-65535')
        self.port_edit.setText(Common.proxy_port)

        self.user_label.setText("Username: ")
        self.user_edit.setPlaceholderText('Optional')

        self.password_label.setText('  Password: ')
        self.password_edit.setPlaceholderText('Optional')
        self.password_edit.setMaximumWidth(250)
        self.password_edit.setMaximumHeight(25)

    def proxy_option_changed(self):
        # socks4 does not require username and password
        if self.proxy_combo.currentText() == 'SOCKS4':
            self.user_label.setEnabled(False)
            self.user_edit.setEnabled(False)
            self.password_label.setEnabled(False)
            self.password_edit.setEnabled(False)
        else:
            self.user_label.setEnabled(True)
            self.user_edit.setEnabled(True)
            self.password_label.setEnabled(True)
            self.password_edit.setEnabled(True)

        Common.proxy_type = self.proxy_combo.currentText()

    def show_proxy_frame(self):
        if self.proxy_checkbox.isChecked():
            self.proxy_frame.show()
            Common.use_proxy = True
        else:
            self.proxy_frame.hide()
            Common.proxy_type = 'None'
            Common.use_proxy = False

    def valid_ip(self, address):
        import socket
        try:
            socket.gethostbyname(address)
            return True
        except socket.error:
            return False

    def valid_port(self, port):
        try:
            if 1 <= int(port) <= 65535:
                return True
            else:
                return False
        except (ValueError, TypeError):
            return False

    def check_valid_proxy_settings(self):
        return (self.valid_ip(self.ip_edit.text()) and
                     self.valid_port(self.port_edit.text()))

    def nextId(self):
        if not Common.use_proxy:
            return self.steps.index('torrc_page')

        else:
            Common.proxy_type = self.proxy_combo.currentText()
            Common.proxy_ip = self.ip_edit.text()
            Common.proxy_port = self.port_edit.text()
            Common.proxy_username = self.user_edit.text()
            Common.proxy_password = self.password_edit.text()

            if not self.check_valid_proxy_settings():
                self.valid_proxy.setWindowModality(Qt.WindowModal)
                self.valid_proxy.exec_()
                return self.steps.index('proxy_wizard_page')

            else:
                return self.steps.index('torrc_page')


class TorrcPage(QWizardPage):
    def __init__(self):
        super(TorrcPage, self).__init__(None)

        self.steps = Common.wizard_steps

        self.title_frame = QFrame(self)
        self.title_layout = QHBoxLayout(self.title_frame)

        self.title_label = QLabel()
        self.title_layout.addWidget(self.title_label, Qt.AlignmentFlag.AlignLeft)

        self.info_frame = QFrame(self)
        self.info_layout = QGridLayout(self.info_frame)
        self.status_label = QLabel()
        Common.bridge_type_label = QLabel()
        self.proxy_type_label = QLabel()
        self.status_text = QLabel()
        self.bridge_text = QLabel()
        self.proxy_text = QLabel()
        self.spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.show_torrc_button = QPushButton()

        self.info_layout.addWidget(self.status_label, 0, 0, Qt.AlignmentFlag.AlignLeft)
        self.info_layout.addWidget(Common.bridge_type_label, 1, 0, Qt.AlignmentFlag.AlignLeft)
        self.info_layout.addWidget(self.proxy_type_label, 2, 0, Qt.AlignmentFlag.AlignLeft)
        self.info_layout.addWidget(self.status_text, 0, 1, Qt.AlignmentFlag.AlignLeft)
        self.info_layout.addWidget(self.bridge_text, 1, 1, Qt.AlignmentFlag.AlignLeft)
        self.info_layout.addWidget(self.proxy_text, 2, 1, Qt.AlignmentFlag.AlignLeft)
        self.info_layout.addItem(self.spacer, 0, 2)
        self.info_layout.addWidget(self.show_torrc_button, 2, 3, Qt.AlignmentFlag.AlignRight)

        self.torrc_frame = QFrame()
        self.torrc_layout = QVBoxLayout(self.torrc_frame)
        self.torrc_text = QTextBrowser(self)
        self.torrc_layout.addWidget(self.torrc_text, 2)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.title_frame)
        self.layout.addWidget(self.info_frame)
        self.layout.addWidget(self.torrc_frame)
        self.setLayout(self.layout)

        self.show_detail = False
        self.setup_ui()

    def setup_ui(self):
        font_title = Common.font_title
        font_option = Common.font_option

        self.title_frame.show()
        self.info_frame.show()

        self.title_label.setText('Summary')
        self.title_label.setFont(font_title)

        self.status_label.setText("Status: ")
        self.status_text.setFont(font_option)

        Common.bridge_type_label.setText("Bridge type: ")
        self.bridge_text.setFont(font_option)

        self.proxy_type_label.setText("Proxy type: ")
        self.proxy_text.setFont(font_option)

        self.show_torrc_button.setEnabled(True)
        self.show_torrc_button.setText('Show torrc')
        self.show_torrc_button.clicked.connect(self.detail)

        self.torrc_text.setVisible(self.show_detail)
        self.torrc_text.setLineWrapMode(QTextBrowser.NoWrap)

    def nextId(self):
        return self.steps.index('tor_status_page')

    def detail(self):
        self.show_detail = not self.show_detail
        self.torrc_text.setVisible(self.show_detail)
        if self.show_detail:
            self.show_torrc_button.setText('&Hide')
        else:
            self.show_torrc_button.setText('&Show torrc')


class TorStatusPage(QWizardPage):
    def __init__(self):
        super(TorStatusPage, self).__init__()
        self.steps = Common.wizard_steps
        self.bootstrap_text = QLabel(self)
        self.text = QLabel(self)
        self.bootstrap_progress = QProgressBar(self)

        self.layout = QGridLayout()
        self.layout.addWidget(self.text, 0, 1, 1, 2)
        self.layout.addWidget(self.bootstrap_progress, 1, 1, 1, 1)
        self.setLayout(self.layout)

        self.setup_ui()

    def setup_ui(self):
        font_description_main = Common.font_description_main

        self.text.setFont(font_description_main)
        self.text.setWordWrap(True)
        self.text.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.text.setMinimumSize(0, 290)

        self.bootstrap_progress.setMinimumSize(400, 0)
        self.bootstrap_progress.setMinimum(0)
        self.bootstrap_progress.setMaximum(100)
        self.bootstrap_progress.setVisible(False)


class AnonConnectionWizard(QWizard):
    def __init__(self):
        super(AnonConnectionWizard, self).__init__()

        """
        Rationalize code.
        If torrc_file_path does not exist, write a torrc template at the start of the app.
        Therefore repair_torrc.py in no longer needed, as well as tor_config_sane
        Since we are confident that a torrc file exists,  we can avoid all the
        " if os.path.exists(self.torrc_file_path):" in the whole package.
        """
        if os.path.exists(Common.torrc_file_path):
            pass
        else:
            args = ['None', 'None', 'None']
            torrc_gen.gen_torrc(args)

        self.steps = Common.wizard_steps

        self.connection_main_page = ConnectionMainPage()
        self.addPage(self.connection_main_page)

        self.bridge_wizard_page = BridgesWizardPage()
        self.addPage(self.bridge_wizard_page)

        self.proxy_wizard_page = ProxyWizardPage()
        self.addPage(self.proxy_wizard_page)

        self.torrc_page = TorrcPage()
        self.addPage(self.torrc_page)

        self.tor_status_page = TorStatusPage()
        self.addPage(self.tor_status_page)

        self.bridges = Common.bridges
        self.proxy_type = ''
        self.tor_status = ''
        self.bootstrap_done = False

        self.reply = None
        self.tor_status_result = None
        translation = _translations(Common.translations_path, 'anon-connection-wizard')
        self._ = translation.gettext

        self.args = torrc_gen.parse_torrc()

        Common.bridge_type = self.args[0]
        Common.proxy_type = self.args[1]
        index = self.proxy_wizard_page.proxies.index(Common.proxy_type)
        self.proxy_wizard_page.proxy_combo.setCurrentIndex(index)
        self.proxy_wizard_page.ip_edit.setText(str(self.args[2]))
        self.proxy_wizard_page.port_edit.setText(str(self.args[3]))
        self.proxy_wizard_page.user_edit.setText(str(self.args[4]))
        self.proxy_wizard_page.password_edit.setText(str(self.args[5]))

        Common.use_default_bridges = Common.bridge_type in Common.default_bridges
        Common.use_custom_bridges = Common.bridge_type == 'Custom bridges'
        Common.use_proxy = not Common.proxy_type == 'None'

        if Common.use_custom_bridges:
        # Retrieve custom bridges
            # if os.path.exists(Common.torrc_file_path):
            with open(Common.torrc_file_path, 'r') as f:
                if '# Custom' in f.read():
                    self.bridge_wizard_page.custom_bridges.clear()
                    f.seek(0)
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('Bridge'):
                            ## The '[6:]' trims off the first 6 characters of
                            ## the string, i.e. the substring 'Bridge'.
                            ##
                            ## TODO: Is there a space here we should be
                            ## trimming off too?
                            line = line.strip('\n')[6:]
                            self.bridge_wizard_page.custom_bridges.append(line)
            f.close()
            self.bridge_wizard_page.custom_bridges.moveCursor(QtGui.QTextCursor.Start)

        if Common.use_default_bridges or Common.use_custom_bridges:
                self.bridge_wizard_page.bridges_checkbox.setChecked(True)

        if Common.use_default_bridges or Common.use_custom_bridges or Common.use_proxy:
            self.connection_main_page.configure_option.setChecked(True)
        else:
            self.connection_main_page.connect_option.setChecked(True)

        self.proxy_wizard_page.proxy_checkbox.setChecked(Common.use_proxy)

        self.setup_ui()

    def setup_ui(self):
        # Retrieve previous settings
        self.bridge_wizard_page.bridges_frame.setVisible(self.bridge_wizard_page.bridges_checkbox.isChecked())

        self.setWindowIcon(QtGui.QIcon("/usr/share/anon-connection-wizard/advancedsettings.ico"))
        self.setWindowTitle('Anon Connection Wizard')
        self.setMinimumSize(500, 420)

        self.button(QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QWizard.NextButton).clicked.connect(self.next_button_clicked)
        self.button(QWizard.CancelButton).clicked.connect(self.cancel_button_clicked)

        self.button(QWizard.BackButton).hide()
        self.button(QWizard.BackButton).setEnabled(False)

        self.button(QWizard.FinishButton).clicked.connect(self.finish_button_clicked)

        self.button(QWizard.CancelButton).show()
        self.button(QWizard.CancelButton).setEnabled(True)
        self.button(QWizard.CancelButton).setText('Quit')
        self.exec_()

    def update_bootstrap(self, bootstrap_phase, bootstrap_percent):
        self.tor_status_page.bootstrap_progress.setValue(bootstrap_percent)
        if bootstrap_percent == 100:
            self.tor_status_page.text.setText('<p><b>Tor bootstrapping done</b></p>Bootstrap phase: {0}'
                                              .format(bootstrap_phase))
            self.bootstrap_done = True
            self.show_finish_button()
        else:
            self.tor_status_page.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: {0}'
                                              .format(bootstrap_phase))

        if bootstrap_phase == 'no_controller':
            self.bootstrap_thread.terminate()
            buttonReply = QMessageBox.warning(self, 'Tor Controller Not Constructed', 'Tor controller \
                                              cannot be constructed.')
            if buttonReply == QMessageBox.Ok:
                sys.exit(1)

        elif bootstrap_phase == 'cookie_authentication_failed':
            self.bootstrap_thread.terminate()
            buttonReply = QMessageBox(QMessageBox.Warning, 'Tor Controller Authentication Failed', '''Tor allows
                                              for authentication by reading it a cookie file, but we cannot read
                                              that file (probably due to permissions)''', QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                sys.exit(1)

    def next_button_clicked(self):
        if self.currentId() == self.steps.index('connection_main_page'):
            self.button(QWizard.CancelButton).show()
            self.button(QWizard.FinishButton).hide()

        if self.currentId() == self.steps.index('torrc_page'):
            self.button(QWizard.BackButton).show()
            self.button(QWizard.CancelButton).show()
            self.button(QWizard.FinishButton).hide()

            self.write_torrc()

            if not Common.disable_tor:
                self.torrc_page.status_text.setText('Tor will be enabled.')
                if (not Common.use_default_bridges) and (not Common.use_custom_bridges):
                    self.torrc_page.bridge_text.setText('None Selected')
                else:
                    self.torrc_page.bridge_text.setText(Common.bridge_type)

                torrc_text = open(Common.torrc_file_path).read()
                self.torrc_page.torrc_text.setPlainText(torrc_text)

            if not Common.use_proxy:
                self.torrc_page.proxy_text.setText('None Selected')
            else:
                if Common.proxy_type == 'HTTP / HTTPS':
                    self.torrc_page.proxy_text.setText('HTTP(S)  {0} : {1}'.format(
                        Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS4':
                    self.torrc_page.proxy_text.setText('Socks4  {0} : {1}'.format(
                        Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS5':
                    self.torrc_page.proxy_text.setText('Socks5  {0} : {1}'.format(
                        Common.proxy_ip, Common.proxy_port))

        if self.currentId() == self.steps.index('tor_status_page'):
            self.tor_status_page.text.setText('')
            self.button(QWizard.BackButton).show()
            self.button(QWizard.CancelButton).show()
            self.button(QWizard.FinishButton).hide()

            '''Arranging different tor_status_page according to the value of disable_tor.'''
            if not Common.disable_tor:
                # if os.path.exists(Common.torrc_file_path):
                ## Move the tmp file to the real .conf only when user
                ## clicks the connect button. This may overwrite the
                ## previous .conf, but it does not matter.
                cat(Common.acw_comm_file_path)
                content = open(Common.torrc_file_path).read()
                write_to_temp_then_move(content)

                self.tor_status_page.bootstrap_progress.show()

                self.tor_status_result = tor_status.set_enabled()
                self.tor_status = self.tor_status_result[0]
                self.tor_status_code = str(self.tor_status_result[1])

                if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                    self.tor_status_page.bootstrap_progress.show()
                    self.bootstrap_thread = tor_bootstrap.TorBootstrap(self)
                    self.bootstrap_thread.signal.connect(self.update_bootstrap)
                    self.bootstrap_thread.start()

                elif self.tor_status == 'cannot_connect':
                    print('tor_status: ' + self.tor_status + self.tor_status_code, file=sys.stderr)
                    self.tor_status_page.bootstrap_progress.hide()
                    self.tor_status_page.text.setText('<p><b>Tor failed to (re)start.</b></p> \
                        <p>Job for tor@default.service failed because the control process \
                        exited with error code.</p>' +
                        'Error Code: ' + self.tor_status_code + '\n' +
                        '<p>Often, this is because one of your torrc file(s) has corrupted settings.</p>' +
                        '<p>See "systemctl status tor@default.service" and \
                        "journalctl -xe" for details.</p>' +
                        '<p>You may not be able to use any network facing application for now.</p>')

                else:
                    print('Unexpected tor_status: ' + self.tor_status + '\n' +
                          "Error Code: " + self.tor_status_code, file=sys.stderr)
                    # display error message on GUI
                    self.tor_status_page.bootstrap_progress.hide()
                    self.tor_status_page.text.setText('<p><b>Unexpected Exception.</b></p> \
                        <p>You may not be able to use any network facing application for now.</p> \
                        Unexpected exception reported from tor_status module:i ' + self.tor_status \
                        + '\n' + "Error Code:" + self.tor_status_code)

            else:
                self.tor_status = tor_status.set_disabled()

                self.tor_status_page.bootstrap_progress.hide()
                self.tor_status_page.text.show()
                self.tor_status_page.text.setText(info.set_disabled())
                self.show_finish_button()

    def write_torrc(self):
        args = []

        if Common.use_default_bridges:
            args.append(Common.bridge_type)
        else:
            args.append('None')

        if Common.use_custom_bridges:
            args.append(Common.custom_bridges)
        else:
            args.append('None')

        if Common.use_proxy:
            args.append(Common.proxy_type)
            args.append(self.proxy_wizard_page.ip_edit.text())
            args.append(self.proxy_wizard_page.port_edit.text())

            if not Common.proxy_username == 'None':
                args.append(Common.proxy_username)
            else:
                args.append('')

            if not Common.proxy_password == 'None':
                args.append(Common.proxy_password)
        else:
            args.append('None')

        torrc_gen.gen_torrc(args)

    def back_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
                self.bootstrap_thread = False

                if Common.init_tor_status == 'tor_enabled':
                    pass
                elif Common.init_tor_status == 'tor_disabled':
                    tor_status.set_disabled()

        except AttributeError:
            pass

        self.bootstrap_done = False
        self.button(QWizard.FinishButton).hide()
        self.button(QWizard.CancelButton).show()

    def cancel_button_clicked(self):
        if self.bootstrap_thread:
            self.bootstrap_thread.terminate()
            tor_status.set_disabled()

        # recover Tor to the initial status before the starting of anon_connection_wizard
        if Common.init_tor_status == 'tor_enabled':
            pass
        elif Common.init_tor_status == 'tor_disabled':
            tor_status.set_disabled()

    def finish_button_clicked(self):
        # The True indicates the acw has finished successfully
        # TODO: this does not work as expected; even when the cancel button is clicked,
        # the wizard still return True
        return True

    def show_finish_button(self):
        if self.bootstrap_done or Common.disable_tor:
            self.button(QWizard.CancelButton).hide()
            self.button(QWizard.FinishButton).show()
            self.button(QWizard.FinishButton).setFocus()


def main():
    if os.geteuid() == 0:
        print('anon_connection_wizard.py: ERROR: Do not run with sudo / as root!')
        sys.exit(1)

    app = QApplication(sys.argv)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Available styles: "windows", "motif", "cde", "sgi", "plastique" and "cleanlooks"
    # TODO: use customized css instead. Take Tor Launcher's css as a reference
    QApplication.setStyle('plastique')

    AnonConnectionWizard()


if __name__ == "__main__":
    main()
