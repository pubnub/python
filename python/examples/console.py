## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/


import sys
from Pubnub import Pubnub
import threading
from datetime import datetime

from cmd2 import Cmd, make_option, options, Cmd2TestCase
import optparse
import json

import atexit
import os
import readline
import rlcompleter

import pygments
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

lexer = JsonLexer()
formatter = TerminalFormatter()
def highlight(msg):
    return pygments.highlight(msg, lexer, formatter)



historyPath = os.path.expanduser("~/.pubnub_console_history")


def save_history(historyPath=historyPath):
    import readline
    readline.write_history_file(historyPath)

if os.path.exists(historyPath):
    readline.read_history_file(historyPath)

atexit.register(save_history)

of = sys.stdout

color = Cmd()

stop = None

full_date = False


def stop_2(th):
    th._Thread__stop()


def stop_3(th):
    th._stop()


def print_console_2(of, message):
    print >>of, message


def print_console_3(of, message):
    of.write(message)
    of.write("\n")

print_console = None

if type(sys.version_info) is tuple:
    print_console = print_console_2
    stop = stop_2
else:
    if sys.version_info.major == 2:
        print_console = print_console_2
        stop = stop_2
    else:
        print_console = print_console_3
        stop = stop_3


def get_date():
    if full_date is True:
        return color.colorize(datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'), "magenta")
    else:
        return color.colorize(datetime.now().strftime(
            '%H:%M:%S'), "magenta")

def print_ok_normal(msg, channel=None):
    if msg is None:
        return
    chstr = "[" + color.colorize(get_date(), "magenta") + "] "
    chstr += "[" + color.colorize("Channel : " + channel if channel is not None else "", "cyan") + "] " 
    try:
        print_console(of, (chstr + color.colorize(str(msg), "green")))
    except UnicodeEncodeError as e:
        print_console(of, (msg))

    of.flush()


def print_error_normal(msg, channel=None):
    if msg is None:
        return
    chstr = "[" + color.colorize(get_date(), "magenta") + "] "
    chstr += "[" + color.colorize("Channel : " + channel if channel is not None else "", "cyan") + "] " 
    try:
        print_console(of, (chstr + color.colorize(color.colorize(
            str(msg), "red"), "bold")))
    except UnicodeEncodeError as e:
        print_console(of, (msg))
    of.flush()

def print_ok_pretty(msg, channel=None):
    if msg is None:
        return
    chstr = "[" + color.colorize(get_date(), "magenta") + "] "
    chstr += "[" + color.colorize("Channel : " + channel if channel is not None else "", "cyan") + "] " 
    try:
        print_console(of, (chstr + highlight(json.dumps(msg, indent=2))))
    except UnicodeEncodeError as e:
        print_console(of, (msg))

    of.flush()


def print_error_pretty(msg, channel=None):
    if msg is None:
        return
    chstr = "[" + color.colorize(get_date(), "magenta") + "] "
    chstr += "[" + color.colorize("Channel : " + channel if channel is not None else "", "cyan") + "] " 
    try:
        print_console(of, (chstr + color.colorize(color.colorize(
            "ERROR: ", "red"), "bold") +
            highlight(json.dumps(msg, indent=2))))
    except UnicodeEncodeError as e:
        print_console(of, (msg))
    of.flush()

print_ok = print_ok_pretty
print_error = print_error_pretty


class DefaultPubnub(object):
    def handlerFunctionClosure(self, name):
        def handlerFunction(*args, **kwargs):
            print_error("Pubnub not initialized." +
                        "Use init command to initialize")
        return handlerFunction

    def __getattr__(self, name):
        return self.handlerFunctionClosure(name)

pubnub = DefaultPubnub()


def kill_all_threads():
    for thread in threading.enumerate():
        if thread.isAlive():
            stop(thread)


def get_input(message, t=None):
    while True:
        try:
            try:
                command = raw_input(message)
            except NameError:
                command = input(message)
            except KeyboardInterrupt:
                return None

            command = command.strip()

            if command is None or len(command) == 0:
                raise ValueError

            if t is not None and t == bool:
                valid = ["True", "true", "1", 1, "y", "Y", "yes", "Yes", "YES"]
                if command in valid:
                    return True
                else:
                    return False
            if t is not None:
                command = t(command)
            else:
                command = eval("'" + command + "'")

            return command
        except ValueError:
            print_error("Invalid input : " + command)


def _publish_command_handler(channel, message, async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)
    print_ok(pubnub.publish(channel, message,
                            _callback if async is True else None,
                            _error if async is True else None))


def _subscribe_command_handler(channel):

    def _callback(r, ch):
        print_ok(r, ch)

    def _error(r, ch=None):
        print_error(r, ch if ch is not None else channel)

    def _disconnect(r):
        print_ok("DISCONNECTED", r)

    def _reconnect(r):
        print_ok("RECONNECTED", r)

    def _connect(r):
        print_ok("CONNECTED", r)

    pubnub.subscribe(channel, _callback, _error, connect=_connect,
                     disconnect=_disconnect, reconnect=_reconnect)


def _unsubscribe_command_handler(channels):

    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    unsub_list = []
    current_channel_list = pubnub.get_channel_array()

    for channel in channels:
        pubnub.unsubscribe(channel)
        if (channel in current_channel_list):
            unsub_list.append(channel)

        #pubnub.unsubscribe(channel + '-pnpres')
        #if (channel + '-pnpres' in current_channel_list):
        #    unsub_list.append(channel + ' (Presence)')

    if len(unsub_list) > 0:
        print_ok('Unsubscribed from : ' + str(unsub_list))
    else:
        print_error('Not subscribed to : ' + str(channels))


def _grant_command_handler(channel, auth_key, read, write, ttl, async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.grant(channel, auth_key,
                          read, write, ttl,
                          _callback if async is True else None,
                          _error if async is True else None))


def _revoke_command_handler(channel, auth_key, ttl, async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.revoke(channel, auth_key, ttl,
                           _callback if async is True else None,
                           _error if async is True else None))


def _audit_command_handler(channel, auth_key, async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.audit(channel, auth_key,
                          _callback if async is True else None,
                          _error if async is True else None))


def _history_command_handler(channel, count, async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.history(channel, count,
                            _callback if async is True else None,
                            _error if async is True else None))


def _here_now_command_handler(channel, async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.here_now(channel, _callback if async is True else None,
                             _error if async is True else None))


def kill_all_threads():
    for thread in threading.enumerate():
        if thread.isAlive():
            stop(thread)


def get_channel_array():
    channels = pubnub.get_channel_array()

    for channel in channels:
        if "-pnpres" in channel:
            chname = channel.split("-pnpres")[0]
            if chname not in channels:
                continue
            i = channels.index(chname)
            channels[i] = channels[i] + color.colorize("(P)", "blue")
            channels.remove(channel)
    return channels


class DevConsole(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        global pubnub
        self.intro = "For Help type ? or help . " + \
            "To quit/exit type exit" + "\n" + \
            "Commands can also be provided on command line while starting console (in quotes) ex. " + \
            "pubnub-console 'init -p demo -s demo'"
        self.default_channel = None
        self.async = False
        pubnub = Pubnub("demo", "demo")
        self.channel_truncation = 3
        self.prompt = self.get_prompt()
        self.publish_key = "demo"
        self.subscribe_key = "demo"
        self.origin = "pubsub.pubnub.com"
        self.auth_key = None
        self.cipher_key = None
        self.secret_key = "demo"
        self.ssl = False
        self.uuid = None
        self.disable_pretty = False

    def get_channel_origin(self):
        cho = ""
        channels = get_channel_array()
        channels_str = ",".join(channels)
        sl = self.channel_truncation
        if len(channels) > int(sl) and int(sl) > 0:
            cho += ",".join(channels[:int(sl)]) + " " + str(
                len(channels) - int(sl)) + " more..."
        else:
            cho += ",".join(channels)

        if len(channels) > 0:
            cho = color.colorize(cho, "bold") + "@"

        origin = pubnub.get_origin().split("://")[1]
        origin += color.colorize(" (SSL)", "green") if pubnub.get_origin(
        ).split("://")[0] == "https" else ""
        return " [" + cho + color.colorize(origin, "blue") + "] > "

    def get_prompt(self):
        prompt = "[" + get_date() + "]"

        if self.default_channel is not None and len(self.default_channel) > 0:
            prompt += " [default channel: " + color.colorize(
                self.default_channel, "bold") + "]"

        prompt += self.get_channel_origin()
        return prompt

    def precmd(self, line):
        self.prompt = self.get_prompt()
        return line

    #def emptyline(self):
    #    self.prompt = self.get_prompt()

    def cmdloop_with_keyboard_interrupt(self):
        try:
            self.cmdloop()
        except KeyboardInterrupt as e:
            pass
        sys.stdout.write('\n')
        kill_all_threads()

    @options([make_option('-p', '--publish-key', action="store",
                          default=None, help="Publish Key"),
              make_option('-s', '--subscribe-key', action="store",
                          default=None, help="Subscribe Key"),
              make_option('-k', '--secret-key', action="store",
                          default=None, help="cipher Key"),
              make_option('-c', '--cipher-key', action="store",
                          default=None, help="Secret Key"),
              make_option('-a', '--auth-key', action="store",
                          default=None, help="Auth Key"),
              make_option('--ssl-on', dest='ssl', action='store_true',
                          default=False, help="SSL Enabled ?"),
              make_option('-o', '--origin', action="store",
                          default=None, help="Origin"),
              make_option('-u', '--uuid', action="store",
                          default=None, help="UUID"),
              make_option('--disable-pretty-print', dest='disable_pretty', action='store_true',
                          default=False, help="Disable Pretty Print ?")
              ])
    def do_init(self, command, opts):
        global pubnub
        global print_ok
        global print_error
        global print_ok_normal
        global print_error_normal
        global print_error_pretty
        global print_ok_pretty

        self.publish_key = opts.publish_key if opts.publish_key is not None else self.publish_key
        self.subscribe_key = opts.subscribe_key if opts.subscribe_key is not None else self.subscribe_key
        self.secret_key = opts.secret_key if opts.secret_key is not None else self.secret_key
        self.cipher_key = opts.cipher_key if opts.cipher_key is not None else self.cipher_key
        self.auth_key = opts.auth_key if opts.auth_key is not None else self.auth_key
        self.origin = opts.origin if opts.origin is not None else self.origin
        self.uuid = opts.uuid if opts.uuid is not None else self.uuid
        self.ssl = opts.ssl if opts.ssl is not None else self.ssl
        self.disable_pretty = opts.disable_pretty if opts.disable_pretty is not None else self.disable_pretty

        pubnub = Pubnub(self.publish_key,
                        self.subscribe_key,
                        self.secret_key,
                        self.cipher_key,
                        self.auth_key,
                        self.ssl,
                        self.origin,
                        self.uuid)
        self.prompt = self.get_prompt()

        if opts.disable_pretty is True:
            print_ok = print_ok_normal
            print_error = print_error_normal
        else:
            print_ok = print_ok_pretty
            print_error = print_error_pretty

    def do_set_sync(self, command):
        """unset_async
        Unset Async mode"""
        self.async = False

    def do_set_async(self, command):
        """set_async
        Set Async mode"""
        self.async = True

    @options([make_option('-n', '--count', action="store",
                          default=3, help="Number of channels on prompt")
              ])
    def do_set_channel_truncation(self, command, opts):
        """set_channel_truncation
        Set Channel Truncation"""

        self.channel_truncation = opts.count

        self.prompt = self.get_prompt()

    def do_unset_channel_truncation(self, command):
        """unset_channel_truncation
        Unset Channel Truncation"""
        self.channel_truncation = 0
        self.prompt = self.get_prompt()

    def do_set_full_date(self, command):
        global full_date
        """do_set_full_date
        Set Full Date"""
        full_date = True
        self.prompt = self.get_prompt()

    def do_unset_full_date(self, command):
        global full_date
        """do_unset_full_date
        Unset Full Date"""
        full_date = False
        self.prompt = self.get_prompt()

    @options([make_option('-c', '--channel',
                          action="store", help="Default Channel")
              ])
    def do_set_default_channel(self, command, opts):

        if opts.channel is None:
            print_error("Missing channel")
            return
        self.default_channel = opts.channel
        self.prompt = self.get_prompt()

    @options([make_option('-f', '--file', action="store",
                          default="./pubnub-console.log", help="Output file")
              ])
    def do_set_output_file(self, command, opts):
        global of
        try:
            of = file(opts.file, 'w+')
        except IOError as e:
            print_error("Could not set output file. " + e.reason)

    @options([make_option('-c', '--channel', action="store",
                          help="Channel for here now data")
              ])
    def do_here_now(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        _here_now_command_handler(opts.channel, async=self.async)

    @options([make_option('-c', '--channel', action="store",
                          help="Channel for history data"),
              make_option('-n', '--count', action="store",
                          default=5, help="Number of messages")
              ])
    def do_get_history(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        _history_command_handler(opts.channel, opts.count, async=self.async)

    @options([make_option('-c', '--channel', action="store",
                          help="Channel on which to publish")
              ])
    def do_publish(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        if command is None:
            print_error("Missing message")
            return

        try:
            message = json.loads(str(command))
        except ValueError as ve:
            message = str(command)

        _publish_command_handler(opts.channel, message, async=self.async)

    @options([make_option('-c', '--channel', action="store",
                          help="Channel on which to grant"),
              make_option('-a', '--auth-key', dest="auth_key",
                          action="store",
                          help="Auth Key"),
              make_option('-r', '--read-enabled', dest='read',
                          action='store_true',
                          default=False, help="Read ?"),
              make_option('-w', '--write-enabled', dest='write',
                          action='store_true',
                          default=False, help="Write ?"),
              make_option('-t', '--ttl', action="store",
                          default=5, help="TTL"),
              make_option('-p', '--presence', action="store_true",
                          dest="presence",
                          default=False, help="Grant on presence channel ?")
              ])
    def do_grant(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel

        opts.auth_key = pubnub.auth_key \
            if opts.auth_key is None else opts.auth_key

        _grant_command_handler(opts.channel, opts.auth_key,
                               opts.read, opts.write,
                               opts.ttl, async=self.async)

        if opts.presence is True:
            _grant_command_handler(opts.channel + '-pnpres', opts.auth_key,
                                   opts.read, opts.write,
                                   opts.ttl, async=self.async)

    @options([make_option('-c', '--channel', action="store",
                          help="Channel on which to revoke"),
              make_option('-a', '--auth-key', dest="auth_key", action="store",
                          help="Auth Key"),
              make_option('-t', '--ttl', action="store",
                          default=5, help="TTL"),
              make_option('-p', '--presence', action="store_true",
                          dest="presence",
                          default=False, help="Revoke on presence channel ?")
              ])
    def do_revoke(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel

        opts.auth_key = pubnub.auth_key \
            if opts.auth_key is None else opts.auth_key

        _revoke_command_handler(
            opts.channel, opts.auth_key, opts.ttl, async=self.async)

        if opts.presence is True:
            _revoke_command_handler(
                opts.channel + '-pnpres', opts.auth_key,
                opts.ttl, async=self.async)

    @options([make_option('-c', '--channel', action="store",
                          help="Channel on which to revoke"),
              make_option('-a', '--auth-key', dest="auth_key", action="store",
                          help="Auth Key")
              ])
    def do_audit(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel

        opts.auth_key = pubnub.auth_key \
            if opts.auth_key is None else opts.auth_key

        _audit_command_handler(opts.channel, opts.auth_key, async=self.async)

    @options([make_option('-c', '--channel', action="store",
                          help="Channel for unsubscribe"),
              make_option('-a', '--all', action="store_true", dest="all",
                          default=False, help="Unsubscribe from all channels"),
              make_option('-p', '--presence', action="store_true",
                          dest="presence",
                          default=False, help="Unsubscribe from presence events ?")
              ])
    def do_unsubscribe(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel

        if (opts.all is True):
            opts.channel = []
            chs = pubnub.get_channel_array()
            for ch in chs:
                if '-pnpres' not in ch:
                    opts.channel.append(ch)
                elif opts.presence is True:
                    opts.channel.append(ch)

        if opts.channel is None:
            print_error("Missing channel")
            return

        if not isinstance(opts.channel, list):
            ch = []
            ch.append(opts.channel)
            opts.channel = ch

        channels = []
        if opts.presence is True and opts.all is False:
            for c in opts.channel:
                if '-pnpres' not in c:
                    channels.append(c + '-pnpres')

        for c in opts.channel:
            channels.append(c)

        _unsubscribe_command_handler(channels)
        self.prompt = self.get_prompt()

    @options([make_option('-c', '--channel', action="store",
                          help="Channel for subscribe"),
              make_option('-g', '--get-channel-list', action="store_true",
                          dest="get",
                          default=False, help="Get susbcribed channel list"),
              make_option('-p', '--presence', action="store_true",
                          dest="presence",
                          default=False, help="Presence events ?")
              ])
    def do_subscribe(self, command, opts):
        opts.channel = self.default_channel \
            if opts.channel is None else opts.channel
        if opts is None:
            print_error("Missing argument")
            return

        if opts.channel is not None:
            _subscribe_command_handler(opts.channel)

        if opts.presence is True:
            _subscribe_command_handler(opts.channel + '-pnpres')

        if opts.get is True:
            print_ok(get_channel_array())
        self.prompt = self.get_prompt()

    def do_exit(self, args):
        kill_all_threads()
        return -1

    #def do_EOF(self, args):
    #    kill_all_threads()
    #    return self.do_exit(args)

    #def handler(self, signum, frame):
    #    kill_all_threads()


def main():
    app = DevConsole()
    app.cmdloop_with_keyboard_interrupt()

if __name__ == "__main__":
    main()
