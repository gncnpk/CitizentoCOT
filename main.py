#!/usr/bin/env python3

import asyncio
import xml.etree.ElementTree as ET
import uuid
import time
import requests

from configparser import ConfigParser

import pytak
import json

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
        while True:
            activityReports = []
            url = self.config.get('CITIZEN_API_URL')
            poll_interval: int = self.config.get('POLL_INTERVAL')
            r = requests.get(url)
            for i in r.json()['results']:
                activityReports.append({
                    "remarks": i['title'],
                    "latitude": i['latitude'],
                    "longitude": i['longitude'],
                    "uuid": i['key']
                })
            for i in activityReports:
                item = tak_activityReport(i['latitude'], i['longitude'], i['uuid'], i['remarks'], poll_interval)
                await self.handle_data(item)
                await asyncio.sleep(0.1)
            print(f"Added {len(activityReports)} activity reports! Checking in {int(poll_interval) // 60} minutes...")
            await asyncio.sleep(int(poll_interval))


def tak_activityReport(lat, lon, uuid, description, poll_interval):
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
    remarks.text = description
    contact = ET.SubElement(detail, "contact")
    contact.set("callsign", "Activity Report")
    color = ET.SubElement(detail, 'color')
    color.set('argb', '-1')
    usericon = ET.SubElement(detail, 'usericon')
    usericon.set('iconsetpath','6d781afb-89a6-4c07-b2b9-a89748b6a38f/Misc/danger.png')
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