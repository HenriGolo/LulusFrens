import asyncio

import discord

from features import LulusCog
from utilitaires import Embed
from utilitaires.config import config
from utilitaires.json import JsonStore, Transaction


class TempVoice(LulusCog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_id = config['TMP_VOICE_CHANNEL']
        self.bdd = Transaction(JsonStore(config['TMP_VOICE_STORAGE']))

    async def handle_create(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        _before = before.channel is None or str(before.channel.id) != str(self.channel_id)
        _after = after.channel is not None and str(after.channel.id) == str(self.channel_id)
        if _before and _after:
            # Crée un nouveau salon vocal temporaire
            new_channel = await member.guild.create_voice_channel(
                name=member.display_name,
                category=after.channel.category,
            )
            # Déplace l'utilisateur dans le nouveau salon vocal
            await member.move_to(new_channel)
            # update la base de données
            with self.bdd as data:
                data[str(new_channel.id)] = member.id
            await config.channel_logs.send(
                embed=Embed(
                    title='Création de salon vocal',
                    description=new_channel.mention,
                    color=0x00ff00,
                ),
            )

    async def handle_leave(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        bchannel: discord.VoiceChannel = before.channel
        if bchannel is not None:
            with self.bdd as data:
                _before = str(bchannel.id) in data
                _after = after.channel is None or bchannel.id != after.channel.id
                if _before and _after:
                    if len(bchannel.members) == 0:
                        del data[str(bchannel.id)]
                        await bchannel.delete(reason='Vocal temporaire vide')
                        await config.channel_logs.send(
                            embed=Embed(
                                title='Suppression de salon vocal',
                                description=bchannel.name,
                                color=0x00ff00,
                            ),
                        )
                    elif str(data[str(bchannel.id)]) == str(member.id):
                        old_owner = data[str(bchannel.id)]
                        new_owner = bchannel.members[0]
                        data[str(bchannel.id)] = new_owner.id
                        if bchannel.name == old_owner.display_name:
                            await bchannel.edit(name=new_owner.display_name)
                        await config.channel_logs.send(
                            embed=Embed(
                                title='Changement de propriétaire',
                                description=f"<@{old_owner}> -> {new_owner.mention}",
                                color=0x00ff00,
                            ),
                        )

    async def on_voice_state_update(self, member, before, after):
        await asyncio.gather(
            self.handle_create(member, before, after),
            self.handle_leave(member, before, after)
        )
