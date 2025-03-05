tail -f /home/asherritt/Desktop/uploader.log

ps aux | grep uploader

journalctl -u cron --no-pager | tail -50

sudo systemctl restart cron

sudo pkill -f uploader/src/main.py
