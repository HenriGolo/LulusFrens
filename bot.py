import datetime
import importlib
import pkgutil
import urllib.parse
from pathlib import Path

from features import *
from utilitaires import now
from utilitaires.config import config


class Lulusfrens(discord.Bot):
    start_time: datetime.datetime
    invite_url: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        plugin_path = Path(__file__).parent / config['FEATURES_DIR']
        for _, module_name, _ in pkgutil.iter_modules([str(plugin_path)]):
            file_path = plugin_path / f"{module_name}.py"
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for obj in module.__dict__.values():
                if inspect.isclass(obj) and issubclass(obj, LulusCog) and obj is not LulusCog:
                    self.add_cog(obj(self))

    async def close(self):
        # L'environnement indique de supprimer le thread
        config_delete = int(config['DELETE_THREAD'])
        # Le thread est vide (juste 1 message : celui de boot)
        aucun_message = len(await config.channel_logs.history(limit=2).flatten()) <= 1
        # Supprimer le thread pour ne garder que les logs intéressants
        if config_delete or aucun_message:
            await config.channel_logs.delete()
        # Sinon archiver proprement
        else:
            await config.channel_logs.send(f"Terminaison en douceur, uptime {now(True) - self.start_time}s")
            await config.channel_logs.archive(True)
        await super().close()

    async def on_ready(self):
        # Début du bot
        self.start_time = now(True)

        self.invite_url = 'https://discord.com/oauth2/authorize?' + urllib.parse.urlencode({
            'client_id': self.user.id,
            'permissions': 8,  # Administrateur https://docs.discord.com/developers/topics/permissions
            'integration_type': 0,
            'scope': 'bot+applications.commands',
        })

        lulusfrens = await self.fetch_guild(config['GUILD_ID'])
        channel_dev = await lulusfrens.fetch_channel(config['CHANNEL_ID_LOGS'])
        thread = await channel_dev.create_thread(name=f"Logs {self.start_time.replace(microsecond=0)}")
        await thread.send(self.invite_url)
        config.set_log_channel(thread)

        # Message de statut du bot
        activity = discord.Activity(name=lulusfrens.name, type=discord.ActivityType.watching)
        await self.change_presence(activity=activity)

        # Print dans la console
        print(f"Connecté en tant que {self.user}")

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.id == self.user.id:
            if after.nick is not None or after.display_name != self.user.name:
                await self.user.edit(username=after.nick)
                await after.edit(nick=None)

    @staticmethod
    async def on_thread_create(thread: discord.Thread):
        await thread.join()

    @staticmethod
    async def on_member_join(member: discord.Member):
        if str(member.guild.id) == config['GUILD_ID']:
            role = await member.guild.fetch_role(int(config['ROLE_ID_EVERYONE']))
            await member.add_roles(role)
        else:
            await member.guild.leave()

    @staticmethod
    async def on_guild_join(guild: discord.Guild):
        if str(guild.id) != config['GUILD_ID']:
            await guild.leave()


if __name__ == '__main__':
    Lulusfrens(intents=discord.Intents.all()).run(token=config['TOKEN'])
