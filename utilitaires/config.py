import os
import sys

import discord
import dotenv


class Config:
    channel_logs: discord.Thread

    def __init__(self, envs):
        values = {
            **os.environ,
            **dotenv.dotenv_values('.env.default'),
            **{
                k: v
                for env in envs
                for k, v in dotenv.dotenv_values(env).items()
            },
        }
        self.values = {k: v for k, v in values.items() if v is not None}
        self.json_format = {}

    def __getitem__(self, item):
        return self.values[item]

    def get(self, item, default=None):
        return self.values.get(item, default)

    def set_log_channel(self, channel: discord.Thread):
        self.channel_logs = channel


config = Config(sys.argv[1:] if len(sys.argv) > 1 else ['.env'])
