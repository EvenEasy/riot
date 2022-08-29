from types import UnionType
from typing import Union
import discord, random, asyncio, config

from basedata import basedata
from admin_functions import admin_functions, user_functions
from riotwatcher import LolWatcher, ApiError
from discord.ext import commands
from discord.utils import get
from discord_components import ButtonStyle, Button,DiscordComponents

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
DiscordComponents(bot)
watcher = LolWatcher(config.RiotApiTOKEN)
db = basedata("basedata.db")

bot.remove_command("help")

#----------------------------------------

@bot.event
async def on_ready():
    print(f"[ {bot.user} ] bot is ready ")
    adminChn=bot.get_channel(config.adminChnID)
    queueChn=bot.get_channel(config.queueCHnID)

    embed = discord.Embed(title="Admin Panel",description=f"Хэй, я **{bot.user.name}**, в этой панели находятся все доступные кнопки для владельца",colour=discord.Color.blurple())
    embed.set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369971935973396/photo_2022-08-25_17-26-17.jpg")
    await adminChn.send(embed=embed,components=[[
        Button(style=ButtonStyle.blue, label="Отправить объявления", custom_id="send_announcement"),
        Button(style=ButtonStyle.blue, label="Объявить Турнир", custom_id="announce_tournament")],[
        Button(style=ButtonStyle.blue, label="Объявить розыгрыш", custom_id="announce_the_raffle"),
        Button(style=ButtonStyle.blue, label="Отправить Новости игры", custom_id="send_game_news")
    ]])

    embed = discord.Embed(title="Admin Panel",description=f"Хэй, я **{bot.user.name}**, в этой панели находятся все доступные кнопки для владельца",colour=discord.Color.blurple())
    embed.set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972351213658/photo_2022-08-25_17-26-13.jpg")
    await queueChn.send(embed=embed,components=[[
        Button(style=ButtonStyle.blue, label="Normal", custom_id="queue_Normal"),
        Button(style=ButtonStyle.blue, label="SoloQ", custom_id="queue_SoloQ")],[
        Button(style=ButtonStyle.blue, label="Flex", custom_id="queue_Flex"),
        Button(style=ButtonStyle.blue, label="ARAM", custom_id="queue_ARAM"),
        Button(style=ButtonStyle.blue, label="Clash", custom_id="queue_Clash")
    ]])

    while True:
        try:
            if len(db.sqlite("SELECT user_id, Exp, Level FROM Users")) >= 1:
                for user_id, activeEXP,Level in db.sqlite("SELECT user_id, Exp, Level FROM Users"):
                    nextLvlEXP = 20 * (Level ** 2)
                    db.sqlite(f"UPDATE Users SET Exp = {activeEXP + 10} WHERE user_id = {user_id}")
                    if activeEXP >= nextLvlEXP:
                        print("NEW LEVEL", Level, user_id)      
                        db.sqlite(f"UPDATE Users SET Level = {Level+1} WHERE user_id = {user_id}")
                        try:
                            user = await bot.fetch_user(user_id)
                        except Exception:
                            continue
                        embed = discord.Embed(title="Поздравляем !", description=f"Поздравляем, вы получили **{Level+1}** уровень", colour=discord.Color.green())
                        #goldEmj = get()
                        embed.add_field(name="Награда", value="300 coint")
                        embed.set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369974595178577/photo_2022-08-25_17-27-49.jpg")
                        try:
                            await user.send(embed=embed)
                        except Exception:
                            print("DM is private")
                        balance = db.get_balance(user_id)
                        print(balance)
                        db.update_balance(user_id, balance[0] + 300, balance[1])
                await asyncio.sleep(3600)
            else:
                return
        except Exception as E:
            print("Error in on_ready",str(E))

@bot.event
async def on_button_click(bttn):
    print(dir(bttn))
    match bttn.component.custom_id.split('_'):
        case ["send","announcement"]:
            await admin_functions.send_event(bttn, config.announcementsChnID)
        case ["announce","tournament"]:
            await admin_functions.send_event(bttn, config.tournamentsChnID)
        case ["announce","the","raffle"]:
            await admin_functions.send_event(bttn, config.raffleChnID)
        case ["send","game","news"]:
            await admin_functions.send_event(bttn, config.newsChnID)
        case ["access", "profile", CODE2FA, region, nickname, user_id]:
            try:
                user_info = watcher.summoner.by_name(region.lower(), " ".join(nickname))
                ranked_stats = watcher.league.by_summoner(region, user_info['id'])
            except Exception as E:
                print("Some error in watcher.summer.by_name -", str(E))
                return
            rank = ranked_stats[0]["tier"].lower().capitalize()
            try:
                role = get(bttn.guild.roles, id=config.ranksRole[rank])
            except Exception as E:
                print("Role not found", str(E))
            user = await bttn.guild.fetch_member(user_id)
            db.registration_user(user_id, user.name,user_info['id'],region)
            try:
                await user.add_roles(role)
            except Exception:
                pass
            await bttn.message.delete()
        case ["not","access", "profile", CODE2FA, user_id]:
            user = await bot.fetch_user(user_id)
            await user.send(embed=discord.Embed(title="Упс...",description="Ваш профиль не подтвердили",colour=discord.Color.red()).set_footer(text="попробуйте еще раз"))
            await bttn.message.delete()
        case ["queue", "SoloQ"]:
            if not db.isInQueue(bttn.author.id):
                try:
                    await bttn.respond(embed=discord.Embed(title="Динамическая очередь", description="ждите набор команды",colour=discord.Color.blurple()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972351213658/photo_2022-08-25_17-26-13.jpg"))
                except Exception:
                    pass
                db.addToQueue(bttn.author.id, "SoloQ", 2)

                team_list = []
                if 2 <= len(db.readQueueByGameType("SoloQ")):
                    for user_id, type, time_size in db.readQueueByGameType("SoloQ"):
                        if len(team_list) < 2:
                            team_list.append(user_id)
                            continue
                        break
                    db.del_user_from_queue(team_list)
                    overwrites = {
                            bttn.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            bttn.guild.me: discord.PermissionOverwrite(read_messages=True),
                        }
                    
                    category = await bttn.guild.create_category("SoloQ", overwrites=overwrites)
                    await category.create_text_channel("SoloQ Chat")
                    await category.create_voice_channel("SoloQ room")
                    for user_id in team_list:
                        try:
                            user = await bot.fetch_user(user_id)
                            await user.send(embed=discord.Embed(title="Команда сформирована", colour=discord.Color.green()).add_field(name="Категория", value="SoloQ"))
                        except Exception as E:
                            print(str(E))
                        try:
                            await category.set_permissions(user, read_messages=True, send_messages=True)
                        except Exception:
                            continue


            else:
                try:
                    await bttn.respond(embed=discord.Embed(title="Динамическая очередь", description="Вы уже в очереди",colour=discord.Color.blurple()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972351213658/photo_2022-08-25_17-26-13.jpg"))
                except Exception:
                    pass
        case ["queue", game_type]:
            if not db.isInQueue(bttn.author.id):
                try:
                    await bttn.respond(embed=discord.Embed(title="Динамическая очередь", description="ждите набор команды",colour=discord.Color.blurple()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972351213658/photo_2022-08-25_17-26-13.jpg"))
                except Exception:
                    pass
                db.addToQueue(bttn.author.id, game_type)

                team_list = []
                if 5 <= len(db.readQueueByGameType(game_type)):
                    for user_id, type, time_size in db.readQueueByGameType(game_type):
                        if len(team_list) < 5:
                            team_list.append(user_id)
                            continue
                        break
                    db.del_user_from_queue(team_list)
                    overwrites = {
                            bttn.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                            bttn.guild.me: discord.PermissionOverwrite(read_messages=True),
                        }                        
                    category = await bttn.guild.create_category(game_type, overwrites=overwrites)
                    await category.create_text_channel(f"{game_type} Chat")
                    await category.create_voice_channel(f"{game_type} room")
                    for user_id in team_list:
                        try:
                            user = await bot.fetch_user(user_id)
                            await user.send(embed=discord.Embed(title="Команда сформирована", colour=discord.Color.green()).add_field(name="Категория", value=game_type))
                        except Exception as E:
                            print(str(E))
                        try:
                            await category.set_permissions(user, read_messages=True, send_messages=True)
                        except Exception:
                            continue

                    
            else:
                try:
                    await bttn.respond(embed=discord.Embed(title="Динамическая очередь", description="Вы уже в очереди",colour=discord.Color.blurple()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972351213658/photo_2022-08-25_17-26-13.jpg"))
                except Exception:
                    pass
        case _:
            print("Button is not found [ ! ]")

@bot.command()
async def помощь(ctx):
    embed=discord.Embed(title="Команды",description="Все доступные команды", colour=discord.Color.blurple())
    embed.add_field(name="!регистрация {region} {nickname}", value="регистрация")
    embed.add_field(name="!профиль", value="показывает ваш профиль")
    embed.add_field(name="!магазин", value="Магазин")
    embed.add_field(name="!купить {number item}", value="купить предмет")
    embed.add_field(name="!открыть все сундуки", value="открыть все сундуки")
    embed.set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369973441724477/photo_2022-08-25_17-25-53.jpg")
    await ctx.send(embed=embed)

@bot.command()
async def профиль(ctx):
    if not db.isReg(ctx.author.id):
        await ctx.send(embed=discord.Embed(title="Регистрация",description="Вы еще не зарегистрированы",colour=discord.Color.red()))
        return
    lol_info = db.get_lol_id(ctx.author.id)
    try:
        ranked_stats = watcher.summoner.by_id(lol_info[1], lol_info[0])
    except Exception as E:
        print(str(E))
        return

    types = {
        "RANKED_FLEX_SR" : "Flex 5x5",
        "RANKED_SOLO_5x5" : "SoloQ"
    }

    Exp,Level = db.sqlite(f"SELECT Exp, Level FROM Users WHERE user_id = {ctx.author.id}")[0]
    embed = discord.Embed(title="Profile", description=f"Player {ctx.author.mention}", colour=discord.Color.random())
    embed.set_thumbnail(url=ctx.author.avatar_url)

    pos = db.sqlite('SELECT user_id FROM Users ORDER BY Level DESC').index((ctx.author.id,)) + 1
    embed.add_field(name="Уровень", value=Level)
    embed.add_field(name="Ед. опыта", value=str(Exp))
    embed.add_field(name="Место", value=f"{pos}/{len(db.sqlite('SELECT user_id FROM Users'))}")

    embed.add_field(name="Никнейм в игре", value=ranked_stats["name"],inline=False)
    for i in watcher.league.by_summoner(lol_info[1], lol_info[0]):
        try:
            embed.add_field(name=types[str(i["queueType"])], value=f"{i['tier'].lower().capitalize()} {i['rank']} **{i['leaguePoints']}** LP")
        except Exception:
            continue

    balance = db.get_balance(ctx.author.id)
    baggoldEMJ = get(ctx.guild.emojis, name="baggold")
    bagcrystalEMJ = get(ctx.guild.emojis, name="bagcrystal")

    trunkEMJ = get(ctx.guild.emojis, name="trunk")
    sphereEMJ = get(ctx.guild.emojis, name="sphere")

    embed.add_field(name="Баланс", value=f"{baggoldEMJ} {balance[0]}  {bagcrystalEMJ} {balance[1]}", inline=False)
    embed.add_field(name="Предметы", value=f"{trunkEMJ} {balance[2]}  {sphereEMJ} {balance[3]}")

    embed.set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369973743730788/photo_2022-08-25_17-25-50.jpg")
    await ctx.send(embed=embed)

@bot.command()
async def магазин(ctx):
    embed=discord.Embed(title="Магазин", description="Специально для вас торговцы собрали вещицы со всей Рунтерры. Чтобы купить, напишите !купить и артикул.", colour=discord.Color.greyple())
    num,items, prices,i=("","","", 1)
    coinEmj = get(ctx.guild.emojis, name="baggold")
    r3Emj = get(ctx.guild.emojis, name="r3")
    for name, price, currency in db.sqlite("SELECT name, price, currency FROM Shop"):
        num+=f"{str(i)}\n"
        items+=f"{r3Emj}{name}\n"
        prices+=f"{r3Emj if currency == 'r3' else coinEmj}{str(price)}\n"
        i+=1
    try:
        embed.add_field(name="№", value=num)
        embed.add_field(name="Предмет", value=items)
        embed.add_field(name="Цена", value=prices)
    except Exception:
        pass
    embed.set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369973961818203/photo_2022-08-25_17-25-45.jpg")
    await ctx.send(embed=embed)

@bot.command()
async def купить(ctx, num : int):
    if not db.isReg(ctx.author.id):
        await ctx.send(embed=discord.Embed(title="Регистрация",description="Вы еще не зарегистрированы",colour=discord.Color.red()))
        return
    items = db.sqlite("SELECT * FROM Shop")
    if len(items)+1 < num or num == 0:
        await ctx.send(embed=discord.Embed(title="Упс...",description="элемент не найден",colour=discord.Color.red()))
        return
    item,price, currency = items[num-1]
    fullBalance = db.get_balance(ctx.author.id)
    balance = fullBalance[0] if currency == 'baggold' else fullBalance[1]

    if balance < price:
        await ctx.send(embed=discord.Embed(title="Упс...",description="На балансе недостаточно монет",colour=discord.Color.red()))
        return
        #Congratulations, you have purchased an item
    match currency:
        case "r3":
            db.update_balance(ctx.author.id, fullBalance[0], balance - price)
        case _:
            db.update_balance(ctx.author.id, balance - price, fullBalance[1])
    try:
        role = get(ctx.guild.roles, name=item)
        await ctx.author.add_roles(role)
    except Exception as E:
        print("Buy error", str(E))
    await ctx.send(embed=discord.Embed(title="Поздравляю !",description=f"Поздравляю, вы купили **{item}**",colour=discord.Color.green()))

@bot.command()
async def открыть(ctx, *args):
    if not db.isReg(ctx.author.id):
        await ctx.send(embed=discord.Embed(title="Регистрация",description="Вы еще не зарегистрированы",colour=discord.Color.red()))
        return
    if args == ("все", "сундуки"):
        numberCase = db.get_balance(ctx.author.id)[2]
        if numberCase <= 0:
            await ctx.send(embed=discord.Embed(title="Упс...",description="У вас 0 сундуков",colour=discord.Color.red()))
            return
        msg = await ctx.send(embed=discord.Embed(title="Открываю сундуки", description=f"Открываю все {numberCase} сундуков", colour=discord.Color.greyple()))
        subjects = {}
        baggoldEMJ = get(ctx.guild.emojis, name="baggold")
        bagcrystalEMJ = get(ctx.guild.emojis, name="bagcrystal")
        for i in range(int(numberCase)):
            subject, type = user_functions.open_case()
            if type in subjects:
                if 'role' in type:
                    subjects[type].append(subject)
                else:
                    subjects[type] += subject
            else:
                if 'role' in type:
                    subjects[type] = [subject]
                else:
                    subjects[type] = subject
        db.sqlite(f"UPDATE Users SET trunks = 0 WHERE user_id = {ctx.author.id}")
        print(subjects)
        embed=discord.Embed(title="Вы открыли все сундуки",description=f"Вы открыли все {numberCase} сундуков\n\n**Вам выпало!**" ,colour=discord.Color.green())
        for key in subjects.keys():

            if 'role' in key:
                arr = []
                for role_id in subjects[key]:
                    role = get(ctx.guild.roles, id=int(role_id))
                    if role.mention in arr: continue
                    await ctx.author.add_roles(role)
                    arr.append(role.mention)
                subj = ', '.join(arr)
                print(subj)
            else:
                subj = subjects[key]
                balance = db.get_balance(ctx.author.id)
                db.update_balance(ctx.author.id, balance[0] + int(subj) if key == 'coins' else balance[0], balance[1] + int(subj) if key == 'crystal' else balance[1])
            embed.add_field(name=key.title(), value=f"{baggoldEMJ if key == 'coins' else bagcrystalEMJ if key == 'crystal' else ''} {subj}")
            print("field added")
        await msg.edit(embed=embed)


@bot.command()
async def регистрация(ctx, region, *nickname):
    if db.isReg(ctx.author.id):
        await ctx.send(embed=discord.Embed(title="Регистрация",description="Вы уже зарегистрированы",colour=discord.Color.green()))
        return
    try:
        user_info = watcher.summoner.by_name(region.lower(), " ".join(nickname))
        my_ranked_stats = watcher.league.by_summoner(region, user_info['id'])
        await ctx.send(my_ranked_stats)
    except Exception as E:
        print(str(E))
        await ctx.send(embed=discord.Embed(title="Упс...",description=f"""Нет в игре игрока с ником **{' '.join(nickname)}** (регион {region})
Проверьте внимательно правильно ли вы вписали ваш **Регион** и **никнейм**, и попробуйте еще раз""",colour=discord.Color.red()))
        return
    CODE2FA = random.choice(range(100000, 999999))
    await ctx.author.send(embed=discord.Embed(title="Верификационный код", description=f"Отправьте заявку в друзья и этот код Игроку **RERO**", colour=discord.Color.green()).add_field(name="Код", value=f"{CODE2FA}"))
    await bot.get_channel(config.adminChnID).send(embed=discord.Embed(title="Подтвердить профиль", description=f"От : **{ctx.author.mention}**\nРегион : **{region}**\nНикнейм в игре : **{' '.join(nickname)}**\nВерификационный код : **{CODE2FA}**",colour=discord.Color.blurple()), components=[[
        Button(style=ButtonStyle.green, label="Подтвердить профиль", custom_id=f"access_profile_{CODE2FA}_{region}_{' '.join(nickname)}_{ctx.author.id}",emoji="✅")],[
        Button(style=ButtonStyle.red, label="не подтверждать профиль", custom_id=f"not_access_profile_{CODE2FA}_{ctx.author.id}",emoji="❌")
    ]])
#    await ctx.send(embed=discord.Embed(title="Шаг 1",description=f"""Подтвердите свой игровой аккаунт через нашу систему,
#проверяйте статистику и получайте серверные награды за игры в
#League of Legends. Напишите команду в канал #команды:

#!регистрация RU ваш никнейм - для русского сервера;
#!регистрация EUW ваш никнейм - для западного сервера.


#Убедитесь, что в разделе Конфиденциальность настроек
#вашего аккаунта Discord разрешены личные сообщения от
#участников сервера. Без этого {bot.user.mention} на сможет отправить вам
#код в личные сообщения.
#""",colour=discord.Color.green()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369973164916847/photo_2022-08-25_17-25-57.jpg"))
#    await ctx.send(embed=discord.Embed(title="Шаг 2",description="""При правильном вводе команды вы получите сообщение от Rift
    
#содержащее код. Отправьте полученный код в личные
#сообщения @Cherry Wolf или @Wise.

#*Обратите внимание, что подтверждение может длиться
#некоторое время, поскольку оно временно выдается вручную.*

#Готово! Поздравляем вас с успешной регистрацией! Не забудьте
#получить игровые роли для удобного поиска игроков.
#""",colour=discord.Color.green()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972921643078/photo_2022-08-25_17-26-00.jpg"))
#    await ctx.send(embed=discord.Embed(title=bot.user.name,description="""
#{bot.user.mention} - это бот, совмещающий игровую статистику привязанного аккаунта в League of Legends к пользователю Discord, обладающий своей экономикой и рейтингом пользователей, которые выражены через серверные и игровые активности, и благодаря которой вы получаете внутреннюю валюту сервера для покупки ролей, фонов профиля и других предметов персонализации.

#Подтвердите игровой аккаунт в нашей системе и начните пользоваться ботом через текстовый канал команды.

#Основная цель бота заключается в помощи участникам сервера в знакомстве и несёт развлекательный характер.
#""",colour=discord.Color.green()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972921643078/photo_2022-08-25_17-26-00.jpg"))
#    await ctx.send(embed=discord.Embed(title="Как поднимать уровень",description="""
#После регистрации в системе бота проверьте свой !профиль. Здесь отображаются ваши предметы и рейтинг на сервере.
#Для повышения своего уровня нужно получать :exp2: ед. опыта,
#они выдаются за активные действия на сервере:
#:br: Сообщения в #общение
#Каждые несколько секунд за сообщения в данный текстовый канал выдается по :exp2: 1 ед. опыта. Перейдите в общение.

#""",colour=discord.Color.green()).set_image(url="https://cdn.discordapp.com/attachments/940593773312897085/1012369972921643078/photo_2022-08-25_17-26-00.jpg"))

@bot.command()
@commands.has_permissions(administrator=True)
async def додать_предмет(ctx, role : discord.Role, price : int, currency : discord.Emoji):
    db.sqlite(f"INSERT INTO Shop VALUES ('{role.name}', {price}, '{currency.name}')")
    msg = await ctx.send("Готово")
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except Exception:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def удалить_предмет(ctx, product: Union[str, discord.Role]):
    print(product.name if product is discord.Role else product)
    db.sqlite(f"DELETE FROM Shop WHERE name = '{product.name if product is discord.Role else product}'")
    msg = await ctx.send("Готово")
    await asyncio.sleep(5)
    try:
        await msg.delete()
    except Exception:
        pass

@bot.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, limit = 10):
    await ctx.channel.purge(limit = limit)

bot.run(config.TOKEN)