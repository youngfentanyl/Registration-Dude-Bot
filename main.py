import discord
from discord.ext import commands
import json
import os
import re
import random
import aiohttp
import string
from flask import Flask
import threading
from datetime import timedelta

app = Flask('')


@app.route('/')
def home():
    return "Bot is alive", 200


def run():
    app.run(host='0.0.0.0', port=8080)


threading.Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True
intents.guild_reactions = True

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
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Streaming(
            name="OpenFront.io",
            url="https://www.twitch.tv/directory/category/openfront"
            )
        )



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


# for the automatic registration
@bot.command()
async def register(ctx, *, args):
    try:
        team_name, team_tag, players_str, subs_str, channel_id_str = [a.strip() for a in args.split('/', 4)]

        players = [p.strip() for p in players_str.split(',')]
        subs = [s.strip() for s in subs_str.split(',')] if subs_str.lower() != "none" else []

        channel_id = int(channel_id_str)
        target_channel = bot.get_channel(channel_id)
        if target_channel is None:
            await ctx.send("❌ Invalid channel ID. Please check and try again.")
            return

        async for msg in target_channel.history(limit=200):
            if msg.embeds:
                embed = msg.embeds[0]
                content = embed.description or ""
                content_lower = content.lower()

                if (team_name.lower() in content_lower or
                    team_tag.lower() in content_lower or
                    any(player.lower() in content_lower for player in players)):
                    await ctx.send("A team with the same name, tag, or one of the players is already registered.")
                    return

        embed = discord.Embed(
            title="New Team Registration",
            description=(
                f"**Team Name:** {team_name}\n"
                f"**Team Tag:** {team_tag}\n"
                f"**Players:** {', '.join(players)}\n"
                f"**Substitutes:** {', '.join(subs) if subs else 'None'}"
            ),
            color=discord.Color.green()
        )
        await target_channel.send(embed=embed)
        await ctx.send("Registration submitted successfully.")

    except Exception as e:
        await ctx.send(f"Error: {e}")

# for the automatic clan wars registration
@bot.command()
async def registerclan(ctx, *, args):
    try:
        clan_name, clan_tag, leader_mention, channel_mention = [a.strip() for a in args.split('/', 3)]

        leader_id = int(leader_mention.strip('<@!>'))
        leader = await bot.fetch_user(leader_id)

        channel_id = int(channel_mention.strip('<#>'))
        target_channel = bot.get_channel(channel_id)
        if target_channel is None:
            await ctx.send("Invalid channel ID. Please check and try again.")
            return

        async for msg in target_channel.history(limit=200):
            if msg.embeds:
                embed = msg.embeds[0]
                lines = (embed.description or "").split('\n')
                existing_name = existing_tag = existing_leader = ""

                for line in lines:
                    if line.lower().startswith("**clan name:**"):
                        existing_name = line.split("**Clan Name:**", 1)[1].strip()
                    elif line.lower().startswith("**clan tag:**"):
                        existing_tag = line.split("**Clan Tag:**", 1)[1].strip()
                    elif line.lower().startswith("**leader:**"):
                        existing_leader = line.split("**Leader:**", 1)[1].strip()

                if (clan_name.lower() == existing_name.lower() or
                    clan_tag.lower() == existing_tag.lower() or
                    leader.mention in existing_leader):
                    await ctx.send("A clan with the same name, tag, or leader is already registered.")
                    return

        embed = discord.Embed(
            title="Clan Registration",
            description=(
                f"**Clan Name:** {clan_name}\n"
                f"**Clan Tag:** {clan_tag}\n"
                f"**Leader:** {leader.mention}\n"
            ),
            color=discord.Color.blue()
        )
        await target_channel.send(embed=embed)
        await ctx.send("Clan registered successfully.")

    except Exception as e:
        await ctx.send(f"Error: {e}")


# only usable in #staff-commands channel, copy an emoji
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
            "Could not fetch the emoji from Discord CDN. Make sure it's a valid emoji ID."
        )
        return

    try:
        new_emoji = await ctx.guild.create_custom_emoji(name=emoji_name,
                                                        image=image_data)
        await ctx.send(
            f"Emoji `{new_emoji.name}` added successfully! {new_emoji}")
    except discord.Forbidden:
        await ctx.send(
            "I don't have permission to add emojis. Make sure I have **Manage Emojis** permission."
        )
    except discord.HTTPException as e:
        await ctx.send(f"Failed to add emoji: {str(e)}")


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
        ("Director", 1355967438704869426),
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
        await ctx.send("Staff update sent to the thread.")
    except discord.NotFound:
        await ctx.send("Thread not found.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to access the thread.")


# Command to delete all messages from a specific user in the server
@bot.command(name="purge-user")
@commands.has_permissions(manage_messages=True)
async def purge_user(ctx, member: discord.Member):
    confirm_msg = await ctx.send(
        f"Are you sure you want to delete **all messages** from {member.mention} in the server?\n"
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

#give a role to multiple users at once
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
            "You need the **Manage Roles** permission to use this command.")
    else:
        await ctx.send("An error occurred. Please check your command syntax."
                       )


#commands r!online and r!offline to indicate if you're playing or not
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

#commands r!online and r!offline to indicate if you're playing or not
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

#command to get all members with a specific role
@bot.command()
async def getrole(ctx, *, role: discord.Role):
    if not ctx.author.guild_permissions.manage_roles:
        return await ctx.send("You do not have the 'Manage Roles' permission to use this command.")

    members = [member for member in ctx.guild.members if role in member.roles]

    if not members:
        return await ctx.send("No members have this role.")

    if len(members) > 400:
        return await ctx.send("Too many members have this role (over 400).")

    chunk_size = 40
    chunks = [members[i:i + chunk_size] for i in range(0, len(members), chunk_size)]

    loading_msg = await ctx.send(f"Preparing {len(chunks)} page(s)...")

    for i, chunk in enumerate(chunks, start=1):
        embed = discord.Embed(
            title=f"Members with role: {role.name}",
            description="\n".join(f"{idx + 1 + (i - 1) * chunk_size}. {member.mention}" for idx, member in enumerate(chunk)),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page {i}/{len(chunks)} • Total: {len(members)} member(s)")
        await ctx.send(embed=embed)

    await loading_msg.delete()

#qualify a user, change the thread ID 
@bot.command()
@commands.has_permissions(administrator=True)
async def qualify(ctx, *, args: str):
    try:
        team_name, team_tag, players_raw, subs_raw = args.split("/")
    except ValueError:
        await ctx.send("Format invalide. Utilisation : `r!qualify Nom De La Team/Team Tag/@player1, @player2/@subs or None`")
        return

    players = [member.strip() for member in players_raw.split(",")]
    subs = subs_raw.strip()

    members_to_role = []
    for mention in players:
        if mention.startswith("<@") and mention.endswith(">"):
            user_id = int(mention.strip("<@!>"))
            member = ctx.guild.get_member(user_id)
            if member:
                members_to_role.append(member)

    role_id = 1371850898778751126
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Le rôle avec l’ID spécifié est introuvable.")
        return

    for member in members_to_role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await ctx.send(f"Impossible d’ajouter le rôle à {member.mention} (permissions manquantes).")

    embed = discord.Embed(
        title=f"Team {team_name} just qualified!",
        description=f"**Players:** {', '.join(players)}\n**Substitutes:** {subs}",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Tag: {team_tag}")

    thread_id = 1386349293539037276
    thread = ctx.guild.get_thread(thread_id)
    if not thread:
        await ctx.send("Cant find the thread.")
        return

    await thread.send(embed=embed)
    await ctx.send(f"Qualification worked for **{team_name}**.")

@qualify.error
async def qualify_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be admin to use this command.")

@bot.command()
async def scrambleteams(ctx, num_groups: int, num_teams: int, *, team_names_raw: str):
    team_names = [name.strip() for name in team_names_raw.split(",") if name.strip()]

    if num_teams > 128:
        return await ctx.send("❌ The team limit is 128.")
    if len(team_names) != num_teams:
        return await ctx.send(f"❌ You specified {num_teams} teams but provided {len(team_names)} names.")

    random.shuffle(team_names)

    groups = [[] for _ in range(num_groups)]
    for i, team in enumerate(team_names):
        groups[i % num_groups].append(team)

    embeds = []
    for i in range(0, num_groups, 4):
        embed = discord.Embed(title="Random Team Assignment", color=discord.Color.green())
        for j in range(4):
            if i + j < num_groups:
                group_title = f"Group {i + j + 1}"
                group_teams = "\n".join(groups[i + j])
                embed.add_field(name=group_title, value=group_teams or "No teams", inline=False)
        embeds.append(embed)

    for embed in embeds:
        await ctx.send(embed=embed)

@bot.command(name="extractdata")
async def extractdata(ctx, channel_id: int, keyword: str):
    try:
        parent_channel = bot.get_channel(channel_id)
        if parent_channel is None:
            await ctx.send("Channel or category not found.")
            return

        channels_to_check = []

        if isinstance(parent_channel, discord.CategoryChannel):
            for ch in parent_channel.channels:
                if isinstance(ch, (discord.TextChannel, discord.ForumChannel)):
                    channels_to_check.append(ch)
        elif isinstance(parent_channel, (discord.TextChannel, discord.ForumChannel)):
            channels_to_check.append(parent_channel)
        else:
            await ctx.send("Unsupported channel type.")
            return

        results = []
        count = 1

        for channel in channels_to_check:
            if isinstance(channel, discord.TextChannel):
                messages = [msg async for msg in channel.history(limit=100)]
                for message in messages:
                    if keyword.lower() in message.content.lower():
                        results.append({
                            "content": message.content,
                            "author": message.author.display_name,
                            "channel": channel.name,
                            "id": count
                        })
                        count += 1

            elif isinstance(channel, discord.ForumChannel):
                threads = channel.threads
                for thread in threads:
                    messages = [msg async for msg in thread.history(limit=100)]
                    for message in messages:
                        if keyword.lower() in message.content.lower():
                            results.append({
                                "content": message.content,
                                "author": message.author.display_name,
                                "channel": f"{channel.name} / {thread.name}",
                                "id": count
                            })
                            count += 1

        if not results:
            await ctx.send(f'No messages found containing "{keyword}".')
            return

        embed = discord.Embed(
            title=f'Results for "{keyword}"',
            color=discord.Color.blue()
        )

        for result in results:
            embed.add_field(
                name=f'Message {result["id"]} by {result["author"]} in {result["channel"]}',
                value=result["content"],
                inline=False
            )

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f'Error: {e}')


#give people the "final" role
@bot.command()
@commands.has_permissions(administrator=True)
async def finalpass(ctx, *, args: str):
    try:
        team_name, team_tag, players_raw, subs_raw = args.split("/")
    except ValueError:
        await ctx.send("Format invalide. Utilisation : `r!finalpass Nom De La Team/Team Tag/@player1, @player2/@subs or None`")
        return

    players = [member.strip() for member in players_raw.split(",")]
    subs = subs_raw.strip()

    members_to_role = []
    for mention in players:
        if mention.startswith("<@") and mention.endswith(">"):
            user_id = int(mention.strip("<@!>"))
            member = ctx.guild.get_member(user_id)
            if member:
                members_to_role.append(member)

    role_id = 1393963175984107600  # même rôle que dans qualify
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Le rôle avec l’ID spécifié est introuvable.")
        return

    for member in members_to_role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await ctx.send(f"Impossible d’ajouter le rôle à {member.mention} (permissions manquantes).")

    embed = discord.Embed(
        title=f"Team {team_name} just went to the final!",
        description=f"**Players:** {', '.join(players)}\n**Substitutes:** {subs}",
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Tag: {team_tag}")

    thread_id = 1386349293539037276  # même thread ou tu peux mettre un autre ID
    thread = ctx.guild.get_thread(thread_id)
    if not thread:
        await ctx.send("Cant find the thread.")
        return

    await thread.send(embed=embed)
    await ctx.send(f"Final pass worked for **{team_name}**.")

@finalpass.error
async def finalpass_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be admin to use this command.")
        
#same, just for semi-final
@bot.command()
@commands.has_permissions(administrator=True)
async def semipass(ctx, *, args: str):
    try:
        team_name, team_tag, players_raw, subs_raw = args.split("/")
    except ValueError:
        await ctx.send("Format invalide. Utilisation : `r!semipass Nom De La Team/Team Tag/@player1, @player2/@subs or None`")
        return

    players = [member.strip() for member in players_raw.split(",")]
    subs = subs_raw.strip()

    members_to_role = []
    for mention in players:
        if mention.startswith("<@") and mention.endswith(">"):
            user_id = int(mention.strip("<@!>"))
            member = ctx.guild.get_member(user_id)
            if member:
                members_to_role.append(member)

    role_id = 1371850898778751126  # même rôle que dans qualify et finalpass
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Le rôle avec l’ID spécifié est introuvable.")
        return

    for member in members_to_role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await ctx.send(f"Impossible d’ajouter le rôle à {member.mention} (permissions manquantes).")

    embed = discord.Embed(
        title=f"Team {team_name} just qualified for the semi-finals!",
        description=f"**Players:** {', '.join(players)}\n**Substitutes:** {subs}",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Tag: {team_tag}")

    thread_id = 1386349293539037276  # même thread ou tu peux mettre un autre ID si besoin
    thread = ctx.guild.get_thread(thread_id)
    if not thread:
        await ctx.send("Cant find the thread.")
        return

    await thread.send(embed=embed)
    await ctx.send(f"Semi-final pass worked for **{team_name}**.")

@semipass.error
async def semipass_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be admin to use this command.")

#announce win of the event
@bot.command()
@commands.has_permissions(administrator=True)
async def winpass(ctx, *, args: str):
    try:
        team_name, team_tag, players_raw, subs_raw = args.split("/")
    except ValueError:
        await ctx.send("Format invalide. Utilisation : `r!winpass Nom De La Team/Team Tag/@player1, @player2/@subs or None`")
        return

    players = [member.strip() for member in players_raw.split(",")]
    subs = subs_raw.strip()

    members_to_role = []
    for mention in players:
        if mention.startswith("<@") and mention.endswith(">"):
            user_id = int(mention.strip("<@!>"))
            member = ctx.guild.get_member(user_id)
            if member:
                members_to_role.append(member)

    role_id = 1371850898778751126 
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Le rôle avec l’ID spécifié est introuvable.")
        return

    for member in members_to_role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await ctx.send(f"Impossible d’ajouter le rôle à {member.mention} (permissions manquantes).")

    embed = discord.Embed(
        title=f"🏆 Team {team_name} just WON the tournament!",
        description=f"**Players:** {', '.join(players)}\n**Substitutes:** {subs}",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Tag: {team_tag}")

    thread_id = 1386349293539037276 
    thread = ctx.guild.get_thread(thread_id)
    if not thread:
        await ctx.send("Cant find the thread.")
        return

    await thread.send(embed=embed)
    await ctx.send(f"Victory announced for **{team_name}**!")

@winpass.error
async def winpass_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be admin to use this command.")
        
#announce second place of the event
@bot.command()
@commands.has_permissions(administrator=True)
async def secondpass(ctx, *, args: str):
    try:
        team_name, team_tag, players_raw, subs_raw = args.split("/")
    except ValueError:
        await ctx.send("Format invalide. Utilisation : `r!secondpass Nom De La Team/Team Tag/@player1, @player2/@subs or None`")
        return

    players = [member.strip() for member in players_raw.split(",")]
    subs = subs_raw.strip()

    members_to_role = []
    for mention in players:
        if mention.startswith("<@") and mention.endswith(">"):
            user_id = int(mention.strip("<@!>"))
            member = ctx.guild.get_member(user_id)
            if member:
                members_to_role.append(member)

    role_id = 1371850898778751126
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Le rôle avec l’ID spécifié est introuvable.")
        return

    for member in members_to_role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await ctx.send(f"Impossible d’ajouter le rôle à {member.mention} (permissions manquantes).")

    embed = discord.Embed(
        title=f"🥈 Team {team_name} takes 2nd place!",
        description=f"**Players:** {', '.join(players)}\n**Substitutes:** {subs}",
        color=discord.Color.teal()
    )
    embed.set_footer(text=f"Tag: {team_tag}")

    thread_id = 1386349293539037276
    thread = ctx.guild.get_thread(thread_id)
    if not thread:
        await ctx.send("Cant find the thread.")
        return

    await thread.send(embed=embed)
    await ctx.send(f"2nd place announced for **{team_name}**!")

@secondpass.error
async def secondpass_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be admin to use this command.")

#announce 3rd place for the event
@bot.command()
@commands.has_permissions(administrator=True)
async def thirdpass(ctx, *, args: str):
    try:
        team_name, team_tag, players_raw, subs_raw = args.split("/")
    except ValueError:
        await ctx.send("Format invalide. Utilisation : `r!thirdpass Nom De La Team/Team Tag/@player1, @player2/@subs or None`")
        return

    players = [member.strip() for member in players_raw.split(",")]
    subs = subs_raw.strip()

    members_to_role = []
    for mention in players:
        if mention.startswith("<@") and mention.endswith(">"):
            user_id = int(mention.strip("<@!>"))
            member = ctx.guild.get_member(user_id)
            if member:
                members_to_role.append(member)

    role_id = 1371850898778751126
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send("Le rôle avec l’ID spécifié est introuvable.")
        return

    for member in members_to_role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            await ctx.send(f"Impossible d’ajouter le rôle à {member.mention} (permissions manquantes).")

    embed = discord.Embed(
        title=f"🥉 Team {team_name} takes 3rd place!",
        description=f"**Players:** {', '.join(players)}\n**Substitutes:** {subs}",
        color=discord.Color.orange()
    )
    embed.set_footer(text=f"Tag: {team_tag}")

    thread_id = 1386349293539037276
    thread = ctx.guild.get_thread(thread_id)
    if not thread:
        await ctx.send("Cant find the thread.")
        return

    await thread.send(embed=embed)
    await ctx.send(f"3rd place announced for **{team_name}**!")

@thirdpass.error
async def thirdpass_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to be admin to use this command.")

#for moderators, to warn the chat to change topic
@bot.command(name="warning")
@commands.has_permissions(manage_messages=True)
async def warning(ctx):
    await ctx.message.delete()

    embed = discord.Embed(
        title="Formal Warning",
        description=(
            "[Community Guidelines](https://discord.com/guidelines/)\n\n"
            "\n"
            "> A formal warning has been issued by our moderation team. "
            "We kindly request that you review the community guidelines to prevent any further escalation of moderation actions."
        ),
        color=discord.Color.red()
    )

    await ctx.send(embed=embed)

#SOTW command, needs administrator perm, to announce the SpeedRun Of The Week
difficulties = ["Balanced", "Intense", "Impossible"]
bots_count = [100, 200, 300, 400]
map_list = [
    "World", "Giant World Map", "North America", "South America", "Europe",
    "Europe (Classic)", "Asia", "Africa", "Oceania", "Black Sea", "Britania",
    "Gateway to the Atlantic", "Between Two Seas", "Iceland", "Japan And Neighbors",
    "MENA", "Australia", "Faroe Islands", "Falkland Islands", "Baikal", "Halkidiki",
    "Italia", "Strait Of Gibraltar"
]

def generate_url(key):
    cleaned_key = re.sub(r'[^\w\s]', '', key) 
    formatted_key = cleaned_key.lower().replace(" ", "")
    return f"https://raw.githubusercontent.com/openfrontio/OpenFrontIO/refs/heads/main/resources/maps/{formatted_key}/thumbnail.webp"

@bot.command()
@commands.has_permissions(administrator=True)
async def sotw(ctx, number: int):
    await ctx.message.delete()

    map_name = random.choice(map_list)
    difficulty = random.choice(difficulties)
    bots = random.choice(bots_count)
    image_url = generate_url(map_name)

    embed = discord.Embed(
        title=f"SOTW #{number}",
        color=discord.Color.red()
    )

    embed.add_field(name="🗺️ Map", value=map_name, inline=True)
    embed.add_field(name="🎮 Gamemode", value="Free for All", inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(name="🤖 Bots", value=str(bots), inline=True)
    embed.add_field(name="🎚️ Difficulty", value=difficulty, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    embed.add_field(
        name="\u200b",
        value="All other Options and Settings must stay as default.",
        inline=False
    )

    embed.set_image(url=image_url)

    await ctx.send(embed=embed)
    

def load_token(path="bot-token.txt"):
    with open(path, "r") as file:
        for line in file:
            if line.startswith("TOKEN="):
                return line.strip().split("TOKEN=")[1]
    raise ValueError("No valid TOKEN found in bot-token.txt")


bot.run(load_token())
