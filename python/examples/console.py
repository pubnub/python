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


of=sys.stdout

color = Cmd()

def print_ok(msg, channel=None):
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

def _publish_command_handler(channel, message):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)
    pubnub.publish(channel, message, _callback, _error)


def _subscribe_command_handler(channel):

    def _callback(r):
        print_ok(r, channel)

    def _error(r):
        print_error(r, channel)
    pubnub.subscribe(channel, _callback, _error)


def _unsubscribe_command_handler(channel):

    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)
    pubnub.unsubscribe(channel)


def _grant_command_handler(channel, auth_key, read, write, ttl):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    pubnub.grant(channel, auth_key, read, write, ttl, _callback)


def _revoke_command_handler(channel, auth_key, ttl):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    pubnub.revoke(channel, auth_key, ttl, _callback)


def _audit_command_handler(channel, auth_key):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    pubnub.audit(channel, auth_key, _callback)


def _history_command_handler(channel, count):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    pubnub.history(channel, count, callback=_callback, error=_error)


def _here_now_command_handler(channel):
    def _callback(r):
        print_ok(r)

    def _error(r):
        print_error(r)

    pubnub.here_now(channel, callback=_callback, error=_error)



class DevConsole(Cmd):
    
    def __init__(self):
        Cmd.__init__(self)
        global pubnub
        self.prompt = "(PubNub Console) > "
        self.intro  = "Welcome to PubNub Developer Console!"  ## defaults to None
        self.default_channel = None
        pubnub = Pubnub("demo", "demo")

    def cmdloop(self):
        try:
            Cmd.cmdloop(self)
        except KeyboardInterrupt as e:
            self.cmdloop()


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


    @options([make_option('-c', '--channel', action="store", help="Default Channel")
     ])
    def do_set_default_channel(self, command, opts):

        if opts.channel is None:
            print_error("Missing channel")
            return
        self.default_channel = opts.channel

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

        _here_now_command_handler(opts.channel)

    @options([make_option('-c', '--channel', action="store", help="Channel for history data"),
            make_option('-n', '--count', action="store", default=5, help="Number of messages")
         ])
    def do_history(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        _history_command_handler(opts.channel, opts.count)


    @options([make_option('-c', '--channel', action="store", help="Channel on which to publish"),
                make_option('-m', '--message', action="store", help="Message to be published")
         ])
    def do_publish(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return

        if opts.message is None:
            print_error("Missing message")
            return

        _publish_command_handler(opts.channel,opts.message)

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

        _grant_command_handler(opts.channel,opts.auth_key, opts.read, opts.write, opts.ttl)

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

        _revoke_command_handler(opts.channel,opts.auth_key, opts.ttl)

    @options([make_option('-a', '--auth-key', dest="auth_key", action="store",
                    help="Auth Key")
         ])
    def do_audit(self, command, opts):

        opts.auth_key = pubnub.auth_key if opts.auth_key is None else opts.auth_key

        _audit_command_handler(opts.auth_key)


    @options([make_option('-c', '--channel', action="store", help="Channel for unsubscribe")
         ])
    def do_unsubscribe(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts.channel is None:
            print_error("Missing channel")
            return
        _unsubscribe_command_handler(opts.channel)


    @options([make_option('-c', '--channel', action="store", help="Channel for subscribe")
         ])
    def do_subscribe(self, command, opts):
        opts.channel = self.default_channel if opts.channel is None else opts.channel
        if opts is None:
            print_error("Missing argument")
            return

        if opts.channel is None:
            print_error("Missing channel")
            return

        _subscribe_command_handler(opts.channel)



def main():
    app = DevConsole()
    app.cmdloop()
  
if __name__ == "__main__":
    main()    

