import logging
import os
import pwd
import time
import asyncio

import websockets
from slacker import Slacker

from opsdroid.connector import Connector
from opsdroid.message import Message


class ConnectorSlack(Connector):

    def __init__(self, config):
        """ Setup the connector """
        logging.debug("Starting Slack connector")
        self.token = config["api-token"]
        self.sc = Slacker(self.token)
        self.name = "slack"
        self.bot_name = config["bot-name"]
        self.known_users = {}
        self.running = False

    async def ws_keepalive(self):
        while self.running:
            await asyncio.sleep(120)
            await self.ping()

    async def ping(self):
        if self.running is False:
            return

        self._message_id += 1
        data = {'id': self._message_id,
                'type': 'ping'}
        content = json.dumps(data)
        await self.ws.send(content)

    async def connect(self, opsdroid):
        """ Connect to the chat service """
        logging.debug("Connecting to Slack")

        connection = await self.sc.rtm.start()

        self.ws = await websockets.connect(connection.body['url'])
        self.running = True

        # Fix keepalives as long as we're ``running``.
        asyncio.async(self.ws_keepalive())

        while True:
            content = await self.ws.recv()

            if content is None:
                break

            message = json.loads(content)

            logging.debug(message)

        # if self.sc.rtm_connect():
        #     logging.info("Connected successfully")
        #     while True:
        #         for m in self.sc.rtm_read():
        #             if "type" in m and m["type"] == "message" and "user" in m:
        #
        #                 # Ignore bot messages
        #                 if "subtype" in m and m["subtype"] == "bot_message":
        #                     break
        #
        #                 # Check whether we've already looked up this user
        #                 if m["user"] in self.known_users:
        #                     user_info = self.known_users[m["user"]]
        #                 else:
        #                     user_info = self.sc.api_call("users.info", user=m["user"])
        #                     self.known_users[m["user"]] = user_info
        #
        #                 message = Message(m["text"], user_info["user"]["name"], m["channel"], self)
        #                 opsdroid.parse(message)
        #         time.sleep(0.1)
        # else:
        #     print("Connection Failed, invalid token?")

    async def respond(self, message):
        """ Respond with a message """
        logging.debug("Responding with: " + message.text)
        await self.sc.chat.post_message(message.room, message.text,
                                        as_user=False, username=self.bot_name,
                                        icon_emoji=':robot_face:')
