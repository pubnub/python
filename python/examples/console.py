## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/


import sys
from Pubnub import PubnubAsync as Pubnub
import threading
from datetime import datetime

from cmd2 import Cmd, make_option, options, Cmd2TestCase
import optparse
import json

import atexit
import os
import readline
import rlcompleter

if sys.argv[0] == "screen":
    print "screen"

historyPath = os.path.expanduser("~/.pubnub_console_history")

def save_history(historyPath=historyPath):
    import readline
    readline.write_history_file(historyPath)

if os.path.exists(historyPath):
    readline.read_history_file(historyPath)

atexit.register(save_history)

of=sys.stdout

color = Cmd()

def print_ok(msg, channel=None):
    if msg is None:
        return
    chstr = color.colorize("[" + datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S') + "] ","magenta")
    chstr += color.colorize("[Channel : " + channel + \
        "] " if channel is not None else "", "cyan")
    try:
        print >>of, (chstr + color.colorize(str(msg),"green"))
    except UnicodeEncodeError as e:
        print >>of, (msg)
    of.flush()

def print_error(msg, channel=None):
    if msg is None:
        return
    chstr = color.colorize("[" + datetime.now().strftime(
        '%Y-%m-%d %H:%M:%S') + "] ", "magenta")
    chstr += color.colorize("[Channel : " + channel + \
        "] " if channel is not None else "", "cyan")
    try:
        print >>of, (chstr + color.colorize(color.colorize(str(msg),"red"),"bold"))
    except UnicodeEncodeError as e:
        print >>of, (msg)
    of.flush()

class DefaultPubnub(object):
    def handlerFunctionClosure(self,name):
        def handlerFunction(*args,**kwargs):
            print_error("Pubnub not initialized. Use init command to initialize")
        return handlerFunction
    def __getattr__(self,name):
        return self.handlerFunctionClosure(name)

pubnub=DefaultPubnub()



def kill_all_threads():
    for thread in threading.enumerate():
        if thread.isAlive():
            thread._Thread__stop()

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

def _publish_command_handler(channel, message,async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)
    print_ok(pubnub.publish(channel, message, _callback if async is True else None, _error if async is True else None))


def _subscribe_command_handler(channel):

    def _callback(r,ch):
        print_ok(r, ch)

    def _error(r,ch=None):
        print_error(r, ch if ch is not None else channel)

    def _disconnect(r):
        print_error("DISCONNECTED", r)

    def _reconnect(r):
        print_error("RECONNECTED", r)

    def _connect(r):
        print_error("CONNECTED", r)

    pubnub.subscribe(channel, _callback, _error,connect=_connect, disconnect=_disconnect, reconnect=_reconnect)


def _unsubscribe_command_handler(channels):

    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)
    if not isinstance(channels,list):
        ch = []
        ch.append(channels)
        channels = ch

    for channel in channels:
        pubnub.unsubscribe(channel)


def _grant_command_handler(channel, auth_key, read, write, ttl,async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.grant(channel, auth_key, read, write, ttl, _callback if async is True else None, _error if async is True else None))


def _revoke_command_handler(channel, auth_key, ttl,async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.revoke(channel, auth_key, ttl, _callback if async is True else None, _error if async is True else None))


def _audit_command_handler(channel, auth_key,async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.audit(channel, auth_key, _callback if async is True else None, _error if async is True else None))


def _history_command_handler(channel, count,async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.history(channel, count, _callback if async is True else None, _error if async is True else None))


def _here_now_command_handler(channel,async=False):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    print_ok(pubnub.here_now(channel, _callback if async is True else None, _error if async is True else None))


def kill_all_threads():
    for thread in threading.enumerate():
        if thread.isAlive():
            thread._Thread__stop()


def get_date(full=False):
    if full is True:
        return color.colorize("[" + datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S') + "] ", "magenta")
    else: 
        return color.colorize("[" + datetime.now().strftime(
            '%H:%M:%S') + "] ", "magenta")  


class DevConsole(Cmd):
    
    def __init__(self):
        Cmd.__init__(self)
        global pubnub
        self.intro  = "For Help type ? or help . To quit/exit type exit"  ## defaults to None
        self.default_channel = None
        self.async = False
        pubnub = Pubnub("demo", "demo")
        self.full_date = False
        self.channel_truncation = 3
        self.prompt = self.get_prompt()


    def get_channel_origin(self):
        cho = " ["
        channels = pubnub.get_channel_array()
        channels_str = ",".join(channels)
        sl = self.channel_truncation
        if len(channels) > 0 and sl > 0:
            cho += ",".join(channels[:int(sl)]) + " " + str(len(channels) - int(sl)) + " more..."
        else:
            cho += ",".join(channels)

        if len(channels) > 0:
            cho = color.colorize(cho,"bold") + "@"

        origin = pubnub.get_origin().split("://")[1]
        origin += color.colorize(" (SSL)","green") if pubnub.get_origin().split("://")[0] == "https" else ""
        return cho + color.colorize(origin,"blue") + "] > "


    def get_prompt(self):
        prompt = get_date(self.full_date)

        if self.default_channel is not None and len(self.default_channel) > 0:
            prompt += " [default channel: " + color.colorize(self.default_channel,"bold") + "]"
         
        prompt += self.get_channel_origin()
        return prompt

    def precmd(self, line):
        self.prompt = self.get_prompt()
        return line

    def emptyline(self):
        print('empty line')
        self.prompt = get_date() + " [" + color.colorize(pubnub.get_origin(),"blue") + "] > "

    def cmdloop_with_keyboard_interrupt(self):
        try:
            self.cmdloop()
        except KeyboardInterrupt as e:
            pass
        sys.stdout.write('\n')
        kill_all_threads()

    @options([make_option('-p', '--publish-key', action="store", default="demo", help="Publish Key"),
            make_option('-s', '--subscribe-key', action="store", default="demo", help="Subscribe Key"),
            make_option('-k', '--secret-key', action="store", default="demo", help="cipher Key"),
            make_option('-c', '--cipher-key', action="store", default="", help="Secret Key"),
            make_option('-a', '--auth-key', action="store", default=None, help="Auth Key"),
            make_option('--ssl-on',  dest='ssl', action='store_true', default=False, help="SSL Enabled ?"),
            make_option('-o', '--origin', action="store", default="pubsub.pubnub.com", help="Origin"),   
            make_option('-u', '--uuid', action="store", default=None, help="UUID")
     ])
    def do_init(self, command, opts):
        global pubnub
        pubnub = Pubnub(opts.publish_key,
                opts.subscribe_key,
                opts.secret_key,
                opts.cipher_key,
                opts.auth_key,
                opts.ssl,
                opts.origin,
                opts.uuid)
        self.prompt = self.get_prompt()


    def do_set_sync(self, command):
        """unset_async
        Unset Async mode"""
        self.async = False

    def do_set_async(self, command):
        """set_async
        Set Async mode"""
        self.async = True

    @options([make_option('-n', '--count', action="store", default=3, help="Number of channels on prompt")
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
        """do_set_full_date
        Set Full Date"""
        self.full_date = True
        self.prompt = self.get_prompt()

    def do_unset_full_date(self, command):
        """do_unset_full_date
        Unset Full Date"""
        self.full_date = False
        self.prompt = self.get_prompt()

    @options([make_option('-c', '--channel', action="store", help="Default Channel")
     ])
    def do_set_default_channel(self, command, opts):

        if opts.channel is None:
            print_error("Missing channel")
            return
        self.default_channel = opts.channel
        self.prompt = self.get_prompt()

    @options([make_option('-f', '--file', action="store", default="./pubnub-console.log", help="Output file")
     ])
    def do_set_output_file(self, command, opts):
        global of
        try:
            of = file(opts.file,'w+')
        except IOError as e:
            print_error("Could not set output file. " + e.reason)


    @options([make_option('-c', '--channel', action="store", help="Channel for here now data")
         ])
    def do_here_now(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        _here_now_command_handler(opts.channel,async=self.async)

    @options([make_option('-c', '--channel', action="store", help="Channel for history data"),
            make_option('-n', '--count', action="store", default=5, help="Number of messages")
         ])
    def do_get_history(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        _history_command_handler(opts.channel, opts.count,async=self.async)


    @options([make_option('-c', '--channel', action="store", help="Channel on which to publish")
         ])
    def do_publish(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
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

        _publish_command_handler(opts.channel,message,async=self.async)

    @options([make_option('-c', '--channel', action="store", help="Channel on which to grant"),
                make_option('-a', '--auth-key', dest="auth_key", action="store",
                    help="Auth Key"),
                make_option('-r', '--read-enabled', dest='read', action='store_true', default=False, help="Read ?"),
                make_option('-w', '--write-enabled', dest='write', action='store_true', default=False, help="Write ?"),
                make_option('-t', '--ttl', action="store", default=5, help="TTL")
         ])
    def do_grant(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        opts.auth_key = pubnub.auth_key if opts.auth_key is None else opts.auth_key

        _grant_command_handler(opts.channel,opts.auth_key, opts.read, opts.write, opts.ttl,async=self.async)

    @options([make_option('-c', '--channel', action="store", help="Channel on which to revoke"),
                make_option('-a', '--auth-key', dest="auth_key", action="store",
                    help="Auth Key"),
                make_option('-t', '--ttl', action="store", default=5, help="TTL")
         ])
    def do_revoke(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        opts.auth_key = pubnub.auth_key if opts.auth_key is None else opts.auth_key

        _revoke_command_handler(opts.channel,opts.auth_key, opts.ttl,async=self.async)

    @options([make_option('-c', '--channel', action="store", help="Channel on which to revoke"),
        make_option('-a', '--auth-key', dest="auth_key", action="store",
                    help="Auth Key")
         ])
    def do_audit(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        opts.auth_key = pubnub.auth_key if opts.auth_key is None else opts.auth_key

        _audit_command_handler(opts.channel, opts.auth_key,async=self.async)


    @options([make_option('-c', '--channel', action="store", help="Channel for unsubscribe"),
            make_option('-a', '--all', action="store_true", dest="all",
                default=False, help="Unsubscribe from all channels")
         ])
    def do_unsubscribe(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if (opts.all is True):
            opts.channel = pubnub.get_channel_array()
        if opts.channel is None:
            print_error("Missing channel")
            return
        _unsubscribe_command_handler(opts.channel)
        self.prompt = self.get_prompt()


    @options([make_option('-c', '--channel', action="store", help="Channel for subscribe"),
            make_option('-g', '--get-channel-list', action="store_true", dest="get",
            default=False, help="Get susbcribed channel list")
         ])
    def do_subscribe(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts is None:
            print_error("Missing argument")
            return

        if opts.channel is not None:
            _subscribe_command_handler(opts.channel)

        if opts.get is True:
            print_ok(pubnub.get_channel_array())
        self.prompt = self.get_prompt()

    def do_exit(self, args):
        kill_all_threads()
        return -1

    def do_EOF(self, args):
        kill_all_threads()
        return self.do_exit(args)

    def handler(self, signum, frame):
        kill_all_threads()

def main():
    app = DevConsole()
    app.cmdloop_with_keyboard_interrupt()
  
if __name__ == "__main__":
    main()    

