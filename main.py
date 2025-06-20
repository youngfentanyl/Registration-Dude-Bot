import discord
from discord.ext import commands
import json
import os
import re
import random
from flask import Flask
import threading

app = Flask('')


@app.route('/')
def home():
    return "Bot is alive!", 200


def run():
    app.run(host='0.0.0.0', port=8080)


threading.Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='r!', intents=intents)

CATEGORY_ID = 1356360895575359730
ALLOWED_CHANNEL_ID = 1372625086938480864
TEAM_REGISTRATION_CHANNEL_ID = 1382386828136550460
COUNTER_FILE = "counter.json"
STATUS_CHANNEL_ID = 1383509707179692082
THUMBNAIL_URL = "https://media.discordapp.net/attachments/929062786481414155/1383510435386490960/file_00000000d5e061f588c0f68ad2f70c2c.png?ex=684f0e00&is=684dbc80&hm=516b2eb4487602088f9c93ece51ba26045bf328fe07c5c89d192d0aaf55323e8&=&format=webp&quality=lossless&width=859&height=859"


@bot.event
async def on_ready():
    print(f'Connecté en tant que {bot.user}!')


# checks if the bot is online
@bot.command(name="ping")
async def ping(ctx):
    ping_value = random.randint(20, 100)
    embed = discord.Embed(title="BBNO$#9291 Actual Ping",
                          description=f"Here's my ping:\n`{ping_value} ms`",
                          color=discord.Color.blue())
    await ctx.send(embed=embed)


# will be added soon to open tickets
@bot.command()
async def summermajor2025(ctx):
    if ctx.channel.id != ALLOWED_CHANNEL_ID:
        await ctx.send(
            f"{ctx.author.mention} You can only use this command in <#1372625086938480864>"
        )
        return

    guild = ctx.guild
    author = ctx.author

    category = discord.utils.get(guild.categories, id=CATEGORY_ID)
    if not category:
        await ctx.send("Category not found.")
        return

    overwrites = {
        guild.default_role:
        discord.PermissionOverwrite(view_channel=False),
        author:
        discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me:
        discord.PermissionOverwrite(view_channel=True, send_messages=True),
    }

    channel_name = f"summermajor2025-{author.name.lower()}"
    channel = await guild.create_text_channel(channel_name,
                                              category=category,
                                              overwrites=overwrites)

    embed = discord.Embed(
        title="OFM Tournament Registration",
        description=
        ("Please provide us the following informations:\n"
         "**Team Name** (the name of your team)\n"
         "**Team Tag** (the tag of your team, example [LBU])\n"
         "**The players in your team** (example young_fentanyl and shutcapybara114) "
         "(you must give us the discord usertag of both players or the ticket will be closed)\n"
         "**Substitue players** (optional)"),
        color=discord.Color.blue())

    await channel.send(embed=embed)
    await ctx.send(f"Channel Created: {channel.mention}")

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        print("Missing permission 'delete_messages'.")
    except discord.HTTPException as e:
        print(f"Cant delete messages : {e}")


# Useless for now, will be activate again for next OFM


def load_counter():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        data = json.load(f)
        return data.get("team_count", 0)


def save_counter(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"team_count": count}, f)


team_count = load_counter()


# for the automatic registration, read l.108 to understand how it works
@bot.command()
@commands.has_permissions(manage_messages=True)
async def register(ctx, *, args: str):
    global team_count

    pattern = r"^(.*?)\/(.*?)\/(.*?)\/(.*?)$"
    match = re.match(pattern, args)
    if not match:
        await ctx.send(
            "Invalid Format. Use : `r!register Team Name/Tag/Nickname1, Nickname2/Substitue`"
        )
        return

    team_name = match.group(1).strip()
    team_tag = match.group(2).strip()
    players_raw = match.group(3).strip()
    substitue = match.group(4).strip()

    try:
        player1, player2 = [p.strip() for p in players_raw.split(",", 1)]
    except ValueError:
        await ctx.send("Please separate the two players with a comma `,`.")
        return

    team_count += 1
    save_counter(team_count)

    embed = discord.Embed(title="Registration",
                          description=(f"**Name:** {team_name}\n"
                                       f"**Tag:** {team_tag}\n"
                                       f"**Players:** {player1}, {player2}\n"
                                       f"**Substitue:** {substitue}"),
                          color=discord.Color.green())

    # Envoi dans le channel d'enregistrement
    registration_channel = ctx.guild.get_channel(TEAM_REGISTRATION_CHANNEL_ID)
    if registration_channel:
        await registration_channel.send(embed=embed)
        await ctx.send("✅ Registration submitted successfully.")
    else:
        await ctx.send("❌ Registration channel not found.")

    role_id = 1371850893074501713
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send(
            "⚠️ Registration complete, but the role could not be found.")
        return

    mentions = ctx.message.mentions
    if mentions:
        for user in mentions:
            try:
                await user.add_roles(role)
                await ctx.send(f"✅ {user.mention} has been given the role.")
            except discord.Forbidden:
                await ctx.send(
                    f"❌ I don't have permission to give the role to {user.mention}."
                )
    else:
        await ctx.send(
            "⚠️ No users were mentioned directly, so no roles were assigned.")


# only usable in #staff-commands channel
@bot.command()
async def copy(ctx, emoji_input: str):
    if ctx.channel.id != 1356604820345196574:
        await ctx.send(
            f"{ctx.author.mention} You can only use this command in <#{1356604820345196574}>."
        )
        return

    match = re.match(r"<a?:([a-zA-Z0-9_]+):(\d+)>", emoji_input)
    if match:
        emoji_name = match.group(1)
        emoji_id = match.group(2)
        is_animated = emoji_input.startswith("<a:")
    else:
        if emoji_input.isdigit():
            emoji_id = emoji_input
            emoji_name = f"emoji_{emoji_id}"
            is_animated = False
        else:
            await ctx.send(
                "❌ Invalid emoji format. Provide a custom emoji or a numeric emoji ID."
            )
            return

    for ext in ("png", "gif"):
        url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{ext}"
        async with ctx.bot.http._HTTPClient__session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                extension = ext
                break
    else:
        await ctx.send(
            "❌ Could not fetch the emoji from Discord CDN. Make sure it's a valid emoji ID."
        )
        return

    try:
        new_emoji = await ctx.guild.create_custom_emoji(name=emoji_name,
                                                        image=image_data)
        await ctx.send(
            f"✅ Emoji `{new_emoji.name}` added successfully! {new_emoji}")
    except discord.Forbidden:
        await ctx.send(
            "❌ I don't have permission to add emojis. Make sure I have **Manage Emojis** permission."
        )
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to add emoji: {str(e)}")


#Command to change the channel #people-in-charge
@bot.command()
@commands.has_permissions(administrator=True)
async def chargeupdate(ctx):
    allowed_channel_id = 1355960796667973735
    thread_id = 1372602073014866061

    if ctx.channel.id != allowed_channel_id:
        await ctx.send(
            f"{ctx.author.mention} This command can only be used in <#{allowed_channel_id}>."
        )
        return

    guild = ctx.guild

    roles_info = [
        ("Co-Directors", 1355967438704869426),
        ("OpenFront Ambassadors", 1355967446741291149),
        ("Administrators", 1355990856099827964),
        ("Moderators", 1355990865163849908),
        ("Referees", 1373770270531129434),
        ("Official Casters", 1372575273953919036),
    ]

    seen_members = set()
    role_to_members = {}

    for role_name, role_id in roles_info:
        role = guild.get_role(role_id)
        if not role:
            role_to_members[role_name] = ["*(Role not found)*"]
            continue

        members = []
        for member in sorted(role.members,
                             key=lambda m: m.display_name.lower()):
            if member.id not in seen_members:
                members.append(member.display_name)
                seen_members.add(member.id)

        role_to_members[role_name] = members if members else ["*(None)*"]

    embed = discord.Embed(
        title="📋 People in charge of OpenFront Masters Competitive League",
        color=discord.Color.blue())

    for role_name, members in role_to_members.items():
        embed.add_field(name=role_name,
                        value="\n".join(f"- {name}" for name in members),
                        inline=False)

    try:
        thread = discord.utils.get(ctx.channel.threads, id=thread_id)
        if thread is None:
            thread = await bot.fetch_channel(thread_id)
        await thread.send(embed=embed)
        await ctx.send("✅ Staff update sent to the thread.")
    except discord.NotFound:
        await ctx.send("❌ Thread not found.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to access the thread.")


@bot.command()
async def uptime(ctx):
    embed = discord.Embed(
        title="Here's my uptime",
        description=(
            "I'm online every day from **1PM to 11PM (French time)**.\n"
            "My commands only work during these hours.\n\n"
            "Outside of those hours, I might be sleeping 😴"),
        color=discord.Color.orange())
    await ctx.send(embed=embed)


# Command to delete all messages from a specific user in the server
@bot.command(name="purge-user")
@commands.has_permissions(manage_messages=True)
async def purge_user(ctx, member: discord.Member):
    confirm_msg = await ctx.send(
        f"⚠️ Are you sure you want to delete **all messages** from {member.mention} in the server?\n"
        "React with ✅ to confirm or ❌ to cancel.")

    await confirm_msg.add_reaction("✅")
    await confirm_msg.add_reaction("❌")

    def check(reaction, user):
        return (user == ctx.author and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == confirm_msg.id)

    try:
        reaction, user = await bot.wait_for("reaction_add",
                                            timeout=30.0,
                                            check=check)
    except asyncio.TimeoutError:
        await confirm_msg.edit(content="⏳ Timeout: purge cancelled.")
        return

    if str(reaction.emoji) == "❌":
        await confirm_msg.edit(content="❌ Purge cancelled.")
        return

    # Purge confirmed
    await confirm_msg.edit(
        content=f"🧹 Deleting messages from {member.display_name}...")

    deleted_count = 0
    error_count = 0

    for channel in ctx.guild.text_channels:
        if not channel.permissions_for(ctx.guild.me).read_message_history:
            continue

        try:
            async for message in channel.history(limit=None):
                if message.author == member:
                    try:
                        await message.delete()
                        deleted_count += 1
                    except discord.HTTPException:
                        error_count += 1
        except discord.Forbidden:
            error_count += 1

    await ctx.send(
        f"✅ Done. Deleted {deleted_count} messages from **{member.display_name}**."
        + (f" ⚠️ {error_count} messages couldn't be deleted."
           if error_count else ""))


@bot.command(name="roleregistration")
@commands.has_permissions(manage_roles=True)
async def roleregistration(ctx, role_id: int, member_ids: str):
    guild = ctx.guild
    role = guild.get_role(role_id)

    if not role:
        await ctx.send("❌ Invalid role ID.")
        return

    member_ids_list = [
        mid.strip() for mid in member_ids.split(",") if mid.strip().isdigit()
    ]
    if not member_ids_list:
        await ctx.send("❌ Please provide valid user IDs.")
        return

    added_members = []
    failed_members = []

    for member_id in member_ids_list:
        member = guild.get_member(int(member_id))
        if not member:
            failed_members.append(f"<@{member_id}> *(not found)*")
            continue

        try:
            await member.add_roles(role,
                                   reason=f"Role registration by {ctx.author}")
            added_members.append(member.mention)
        except discord.Forbidden:
            failed_members.append(f"{member.mention} *(permission denied)*")
        except discord.HTTPException:
            failed_members.append(f"{member.mention} *(failed)*")

    embed = discord.Embed(title="📌 Role Registration",
                          color=discord.Color.green())

    if added_members:
        embed.add_field(name="✅ Role added to:",
                        value="\n".join(added_members),
                        inline=False)
    if failed_members:
        embed.add_field(name="⚠️ Failed to add role to:",
                        value="\n".join(failed_members),
                        inline=False)

    await ctx.send(embed=embed)


@roleregistration.error
async def roleregistration_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ You need the **Manage Roles** permission to use this command.")
    else:
        await ctx.send("❌ An error occurred. Please check your command syntax."
                       )


    #command r!online and r!offline to indicate if you're playing or not
@bot.command()
async def online(ctx, flag: str = None):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    embed = discord.Embed(title="**OpenFront**",
                          description=f"{ctx.author.mention}",
                          color=discord.Color.green())
    embed.add_field(name="STATUS", value="🟢 ONLINE", inline=False)

    if flag and len(flag) <= 5:
        embed.add_field(name="Language", value=flag.upper(), inline=False)

    embed.set_footer(text="OpenFront Masters Competitive League")
    embed.set_thumbnail(url=THUMBNAIL_URL)

    for channel in ctx.guild.text_channels:
        if channel.id == STATUS_CHANNEL_ID:
            await channel.send(embed=embed)
            return

    print(
        f"[ERREUR] Salon avec l'ID {STATUS_CHANNEL_ID} introuvable dans ce serveur."
    )


@bot.command()
async def offline(ctx):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        pass

    embed = discord.Embed(title="**OpenFront**",
                          description=f"{ctx.author.mention}",
                          color=discord.Color.red())
    embed.add_field(name="STATUS", value="🔴 OFFLINE", inline=False)

    embed.set_footer(text="OpenFront Masters Competitive League")
    embed.set_thumbnail(url=THUMBNAIL_URL)

    for channel in ctx.guild.text_channels:
        if channel.id == STATUS_CHANNEL_ID:
            await channel.send(embed=embed)
            return

    print(
        f"[ERREUR] Salon avec l'ID {STATUS_CHANNEL_ID} introuvable dans ce serveur."
    )


def load_token(path="bot-token.txt"):
    with open(path, "r") as file:
        for line in file:
            if line.startswith("TOKEN="):
                return line.strip().split("TOKEN=")[1]
    raise ValueError("No valid TOKEN found in bot-token.txt")


bot.run(load_token())
