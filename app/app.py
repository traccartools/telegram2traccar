#!/usr/bin/env python3

import logging
import os
import signal

import requests

from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse

from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters, CallbackContext

import geopy
import geopy.distance

DEFAULT_TRACCAR_HOST = 'http://traccar:8082'

LOGGER = logging.getLogger(__name__)





class Telegram2Traccar():
    def __init__(self, conf: dict):
        # Initialize the class.
        super().__init__()

        self.traccar_host = conf.get("TraccarHost")
        self.traccar_osmand = conf.get("TraccarOsmand")
        telegram_token = conf.get("TelegramToken")
        self.lastposition = {}

        self.application = Application.builder().token(telegram_token).build()
        self.application.add_handler(MessageHandler(filters.LOCATION, self.t_location))
        self.application.add_handler(CommandHandler("start", self.t_start))

    def start(self):
        self.application.run_polling()

    async def t_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text("Device dentifier: %s" % (str(update.message.chat_id)))

    async def t_location(self, update: Update, context: CallbackContext) -> None:
        if update.edited_message:
            message = update.edited_message
        else:
            message = update.message

        LOGGER.debug(f"APRS message received: %s", str(message))

        lat = message.location.latitude
        lon = message.location.longitude
        dev_id = message.chat_id

        d = message.edit_date or message.date
        timestamp = int(datetime.timestamp(d))

        bearing = message.location.heading or 0

        point = geopy.Point(lat, lon)
        lp = self.lastposition.get(dev_id)
        if lp:            
            distance = geopy.distance.distance(point, lp["point"]).m
            speed = round(distance / (d - lp["time"]).total_seconds() * 3.6, 1)
        else:
            speed = 0
        self.lastposition[dev_id] = {"point": point, "time": d}

        altitude = 0

        # extra attributes
        
        query_string = ""
        ml = message.location.to_dict().keys()
        if "live_period" in ml:
            query_string += "&Telegram_share_time=%s" % str(timedelta(seconds=(message.location.live_period - (d - message.date).total_seconds())))

        
        # for attr in ['horizontal_accuracy', 'live_period']:
        #     print (message.location.to_dict().keys())
        #     if attr in message.location.to_dict().keys():
        #         query_string += f"&TELEGRAM_{attr}={message.location[attr]}"

        query_string = f"id={dev_id}&lat={lat}&lon={lon}&altitude={altitude}&bearing={bearing}&speed={speed}&timestamp={timestamp}" + query_string
        self.tx_to_traccar(query_string)

    

    def tx_to_traccar(self, query: str):
        # Send position report to Traccar server
        LOGGER.debug(f"tx_to_traccar({query})")
        url = f"{self.traccar_osmand}/?{query}"
        print(url)
        try:
            post = requests.post(url)
            # logging.debug(f"POST {post.status_code} {post.reason} - {post.content.decode()}")
            if post.status_code == 400:
                logging.warning(
                    f"{post.status_code}: {post.reason}. Please create device with matching identifier on Traccar server.")
                raise ValueError(400)
            elif post.status_code > 299:
                logging.error(f"{post.status_code} {post.reason} - {post.content.decode()}")
        except OSError:
            logging.exception(f"Error sending to {url}")





if __name__ == '__main__':
    log_level = os.environ.get("LOG_LEVEL", "INFO")

    logging.basicConfig(level=log_level)


    def sig_handler(sig_num, frame):
        logging.debug(f"Caught signal {sig_num}: {frame}")
        logging.info("Exiting program.")
        exit(0)

    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)
    
    def OsmandURL(url):
        u = urlparse(url)
        u = u._replace(scheme="http", netloc=u.hostname+":5055", path = "")
        return(urlunparse(u))
        
    config = {}
    config["TraccarHost"] = os.environ.get("TRACCAR_HOST", DEFAULT_TRACCAR_HOST)
    config["TraccarOsmand"] = os.environ.get("TRACCAR_OSMAND", OsmandURL(config["TraccarHost"]))
    config["TelegramToken"] = os.environ.get("TELEGRAM_TOKEN", "")

    T2T = Telegram2Traccar(config)
    T2T.start()
    
