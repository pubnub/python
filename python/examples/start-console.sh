#!/bin/bash

#!/bin/bash -e

BASEDIR=.

if [ ! -d "$BASEDIR/ve" ]; then
    virtualenv -q $BASEDIR/ve --no-site-packages
    $BASEDIR/ve/bin/activate
    echo "Virtualenv created."
fi

chmod 755 $BASEDIR/ve/bin/activate
$BASEDIR/ve/bin/activate

if [ ! -f "$BASEDIR/ve/updated" -o $BASEDIR/requirements.pip -nt $BASEDIR/ve/updated ]; then
    pip install -r $BASEDIR/requirements.pip -E $BASEDIR/ve
    touch $BASEDIR/ve/updated
    echo "Requirements installed."
fi



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
