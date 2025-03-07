Check if Mosquitto Broker is running

sudo systemctl status mosquitto

Check if Mosquitto is Listening on Port 1883
sudo netstat -tulnp | grep 1883

What IP address
hostname -I

sudo python ~/Desktop/RM-Camera-1/broker/src/main.py

libcamera-vid -t 0 --width 2028 --height 1080 --framerate 50 --autofocus-mode auto --exposure auto --gain auto

libcamera-vid -t 0 --width 2028 --height 1080 --framerate 25 --shutter 40000 --gain 8

sudo systemctl restart cron

sudo pkill -f broker/src/main.py    
