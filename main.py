#!/usr/bin/env python3

import asyncio
import xml.etree.ElementTree as ET
import uuid
import time
import requests
import logging
from datetime import datetime, date

from configparser import ConfigParser
from sys import platform

import pytak
import json
color_table = {
    "yellow": "-256",
    "orange": "-35072",
    "red": "-65536",
    "cyan": "-16711681",
    "brown": "-7650029",
    "blue": "-16776961",
    "green": "-16711936",
    "white": "-1",
    "pink": "-65281"
}
cata_table = {
    "Traffic Related": "cyan",
    "Fire": "orange",
    "Wildfire": "orange",
    "Assault / Fight": "brown",
    "Police Related": "blue",
    "Hazardous Condition": "yellow",
    "Gun Related": "brown",
    "Robbery / Theft ": "green",
    "Weapon": "brown",
    "Fire / EMS Activity": "red",
    "Break In": "green",
    "Pursuit / Search": "blue",
    "Rescue": "red",
    "Harassment": "pink"
}
class MySerializer(pytak.QueueWorker):
    """
    Defines how you process or generate your Cursor-On-Target Events.
    From there it adds the COT Events to a queue for TX to a COT_URL.
    """

    async def handle_data(self, data):
        """
        Handles pre-COT data and serializes to COT Events, then puts on queue.
        """
        event = data
        await self.put_queue(event)

    async def run(self, number_of_iterations=-1):
        """
        Runs the loop for processing or generating pre-COT data.
        """
        logger = logging.getLogger('citizentocot')
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
        while True:
            activityReports = []
            url = self.config.get('CITIZEN_API_URL')
            poll_interval: int = self.config.get('POLL_INTERVAL')
            r = requests.get(url)
            today = date.today()
            for i in r.json()['results']:
                incident_seconds = i['ts'] / 1000
                incident_datetime = datetime.fromtimestamp(incident_seconds)
                if incident_datetime.date() == today:
                    updates = []
                    for i2 in i['updates']:
                        update_seconds = i['updates'][i2]['ts'] / 1000
                        update_datetime = datetime.fromtimestamp(update_seconds)
                        if "linux" in platform:
                            update_timestamp = datetime.strftime(update_datetime, '%-I:%M %p')
                        elif "darwin" in platform:
                            update_timestamp = datetime.strftime(update_datetime, '%-I:%M %p')
                        elif "win32" in platform:
                            update_timestamp = datetime.strftime(update_datetime, '%#I:%M %p')
                        else:
                            logger.warning("Unknown OS! Please create a issue on GitHub.")
                            continue
                        updates.append(f"{update_timestamp} - {i['updates'][i2]['text']}")
                    try:
                        color = color_table.get(cata_table.get(i['categories'][0]))
                        if color == None:
                            logger.warning(f"Catagory [{i['categories'][0]}] not found in table! Please create a issue on Github.")
                            color = color_table.get("white")
                    except:
                        logger.debug("Incident has no catagory.")
                        color = color_table.get("white")
                    activityReports.append({
                        "name": i['title'],
                        "latitude": i['latitude'],
                        "longitude": i['longitude'],
                        "uuid": i['key'],
                        "updates": updates,
                        "color": color
                    })
            for i in activityReports:
                logger.debug(f"Creating a CoT Event with these parameters: {(i['latitude'], i['longitude'], i['uuid'], i['name'], i['updates'], i['color'], poll_interval)}")
                item = tak_activityReport(i['latitude'], i['longitude'], i['uuid'], i['name'], i['updates'], i['color'], poll_interval)
                await self.handle_data(item)
                await asyncio.sleep(0.1)
            logger.info(f"Added {len(activityReports)} activity reports! Checking in {int(poll_interval) // 60} minutes...")
            await asyncio.sleep(int(poll_interval))


def tak_activityReport(lat, lon, uuid, name, updates, icon_color, poll_interval):
    event_uuid = uuid
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "a-u-G")
    root.set("uid", event_uuid)
    root.set("how", "h-g-i-g-o")
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set("stale", pytak.cot_time(int(poll_interval)))
    point = ET.SubElement(root, 'point')
    point.set('lat', str(lat))
    point.set('lon', str(lon))
    point.set('hae', '250')
    point.set('ce', '9999999.0')
    point.set('le', '9999999.0')
    detail = ET.SubElement(root, 'detail')
    status = ET.SubElement(detail, 'status')
    status.set('readiness', 'true')
    precisionlocation = ET.SubElement(detail, "precisionlocation")
    precisionlocation.set("altsrc", "DTED0")
    remarks = ET.SubElement(detail, 'remarks')
    remarks.text = '\n'.join(updates)
    contact = ET.SubElement(detail, "contact")
    contact.set("callsign", name)
    color = ET.SubElement(detail, 'color')
    color.set('argb', icon_color)
    usericon = ET.SubElement(detail, 'usericon')
    usericon.set('iconsetpath','ad78aafb-83a6-4c07-b2b9-a897a8b6a38f/Pointers/track-none.png')
    return ET.tostring(root)

async def main():
    """
    The main definition of your program, sets config params and
    adds your serializer to the asyncio task list.
    """

    config = ConfigParser()
    config.read('config.ini')
    config = config['citizentocot']
    # Initializes worker queues and tasks.
    clitool = pytak.CLITool(config)
    await clitool.setup()

    # Add your serializer to the asyncio task list.
    clitool.add_tasks(set([MySerializer(clitool.tx_queue, config)]))
    # Start all tasks.
    await clitool.run()


if __name__ == "__main__":
    asyncio.run(main())