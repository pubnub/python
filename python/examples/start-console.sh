#!/bin/bash
if ! type "screen" > /dev/null; then
    echo "[ERROR] Screen is not installed. Please install screen to use this utility ."
    exit
fi
rm ./pubnub-console.log
touch ./pubnub-console.log
export PYTHONPATH=../..
screen -X -S pubnub-console quit 2>&1 > /dev/null
OS="`uname`"
case $OS in
  [dD]'arwin')
	screen -c config_osx
    ;;
  *) screen -c config ;;
esac
