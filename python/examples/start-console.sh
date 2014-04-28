if ! type "screen" > /dev/null; then
    echo "[ERROR] Screen is not installed. Please install screen to use this utility ."
    exit
fi
rm ./pubnub-console.log
touch ./pubnub-console.log
set PYTHONPATH=../..
screen -c config
