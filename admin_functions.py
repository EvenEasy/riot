import discord, random, asyncio, config

from discord.ext import commands
from discord.utils import get
from discord_components import ButtonStyle, Button,DiscordComponents

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
DiscordComponents(bot)

class admin_functions:
    async def send_event(bttn, chnID):
        try:
            await bttn.respond()
        except Exception:
            pass
        channel = bot.get_channel(chnID)
        msg = await bttn.channel.send(embed=discord.Embed(title="Headline", description="Enter the headline", colour=discord.Color.blurple()))
        try:
            resp = await bot.wait_for("message", check=lambda i:i.channel == bttn.channel,timeout=60)
        except asyncio.TimeoutError:
            await msg.edit(embed=discord.Embed(title="Time is up", description="", colour=discord.Color.red()))
            await asyncio.sleep(7)
            await msg.delete()
            return
        title=resp.content
        await resp.delete()

        await msg.edit(embed=discord.Embed(title="Description", description="Enter the description", colour=discord.Color.blurple()))
        try:
            resp1 = await bot.wait_for("message", check=lambda i:i.channel == bttn.channel, timeout=1800)
        except asyncio.TimeoutError:
            await msg.edit(embed=discord.Embed(title="Time is up",description="" ,colour=discord.Color.red()))
            await asyncio.sleep(7)
            await msg.delete()
            return
        description = resp1.content
        await resp1.delete()
        while True:
            await msg.edit(embed=discord.Embed(title="Image",description="Will you use image?" ,colour=discord.Color.red()), components=[
                [Button(style=ButtonStyle.green,label="Set"), Button(label="No")]
            ])
            embedNews = discord.Embed(title=title, description=description, colour=discord.Color.blurple())
            respImage = await bot.wait_for("button_click", check=lambda i:i.channel == bttn.channel, timeout=600)
            try:
                await respImage.respond()
            except Exception:
                pass
            if respImage.component.label == "Set":
                await msg.edit(embed=discord.Embed(title="Image",description="Set image" ,colour=discord.Color.blurple()), components=[])
                url = await bot.wait_for("message", check=lambda i:i.channel == bttn.channel, timeout=600)
                try:
                    url1 = url.content if url.content != "" else url.attachments[0].url
                except Exception as E:
                    print(f"EXCEPTION - {E}")
                    continue
                embedNews.set_image(url=url1)
                await url.delete()

            await msg.edit(embed=embedNews,
                components=[
                    [Button(style=ButtonStyle.green, label="Send"), Button(style=ButtonStyle.red, label="Delete")]
                ]
            )
            try:
                resp2 = await bot.wait_for("button_click", check=lambda i:i.channel == bttn.channel, timeout=60)
            except asyncio.TimeoutError:
                await msg.edit(embed=discord.Embed(title="Time is up", colour=discord.Color.blurple()))
                await asyncio.sleep(7)
                await msg.delete()
                return
            try:
                await resp2.respond()
            except Exception:
                pass
            if resp2.component.label == "Send":
                await channel.send(embed=embedNews)
                await msg.edit(embed=discord.Embed(title="Great", description=f"The message was sent to channel {channel.mention}", colour=discord.Color.green()), components=[])
                await asyncio.sleep(5)
                await msg.delete()
                return
            elif resp2.component.label == "Delete":
                await msg.delete()
                return
            break

class user_functions:
    def open_case():
        loot = {
            "coins" : {"min" : 500, "max":1000},
            "roles" : ("951419192781996043","1001038508405833749"),
            "rare role" : ("1001037983417368576","940605575736205342"),
            "emerald" : {"min" : 1, "max":10}
        }

        num = (random.randint(1, 1000), random.randint(1, 1000))
        if num[0] <= 700 and num[0] >= 500:
            return (loot["roles"][random.randint(0, len(loot["roles"])-1)], "role")
        elif num[0] <= 30 and num[0] >= 0:
            return (loot["rare role"][random.randint(0, len(loot["roles"])-1)], "rare role")
        elif num[0] <= 900 and num[0] >= 801:
            return (random.randint(loot["emerald"]['min'], loot["emerald"]['max'])*10,"crystal")
        else:
            return (random.randint(loot["coins"]['min'], loot["coins"]['max']), "coins")
