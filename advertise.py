import sqlite3
import discord

from advertise_settings_modal import AdvertisementSettingsModal
from crontabs import delete_cron_job, run_advertisement


async def show_advertise_settings(ctx: discord.Interaction):
    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()
    c.execute('SELECT message, interval, alias, channel_id FROM advetisement WHERE server_id = ?', (ctx.guild.id,))
    results = c.fetchall()
    channel_name = ctx.guild.get_channel(results[0][3]).name if results else None
    conn.close()
    if results:
        for message, interval, alias, channel_id in results:
            embed = discord.Embed(title=f"Channel Settings: {channel_name}", color=discord.Color.blue())
            embed.add_field(name="Message", value=("Set" if message else "Not set"), inline=True)
            embed.add_field(name="Interval", value=f'`{interval}`', inline=True)
            embed.add_field(name="Alias", value=alias, inline=True)
            embed.add_field(name="Channel", value=f'<#{channel_id}>', inline=True)
            await ctx.response.send_message(embed=embed)
    if len(results) == 0:
        await ctx.response.send_message('This server has no advertisement channels set up!', ephemeral=True)


async def link_advertise_channel(ctx: discord.Interaction, channel, alias):
    if not channel.is_news():
        await ctx.response.send_message('This channel is not an announcement channel!', ephemeral=True)
        return

    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()
    # Check if the alias is already in use for this server
    c.execute('SELECT * FROM advetisement WHERE server_id = ? AND alias = ?', (ctx.guild.id, alias))
    if c.fetchone():
        await ctx.response.send_message('This alias is already in use for this server!', ephemeral=True)
        return

    c.execute('INSERT INTO advetisement (channel_id, server_id, alias) VALUES (?, ?, ?)',
              (channel.id, ctx.guild.id, alias))
    conn.commit()
    conn.close()
    embed = discord.Embed(title="Setup Complete", color=discord.Color.green())
    embed.add_field(name="Channel ID", value=channel.id, inline=True)
    embed.add_field(name="Channel Name", value=channel.name, inline=True)
    embed.add_field(name="Alias", value=alias, inline=True)
    embed.add_field(name="Settings command", value="/advertise settings <alias>", inline=False)
    embed.add_field(name="Unlink command", value="/advertise unlink <alias>", inline=False)
    embed.add_field(name="Show Settings command", value="/advertise list", inline=False)
    embed.add_field(name="Help command", value="/advertise help", inline=False)
    await ctx.response.send_message(embed=embed)


async def unlink_advertise_channel(ctx: discord.Interaction, alias):
    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()
    c.execute('DELETE FROM advetisement WHERE server_id = ? AND alias = ?', (ctx.guild.id, alias))
    conn.commit()
    conn.close()

    delete_cron_job(f"{alias}_{ctx.guild.id}")

    await ctx.response.send_message('This channel has been unlinked from advertisement!', ephemeral=True)


async def set_advertise_message(ctx: discord.Interaction):
    alias = ctx.message.content.split(' ')[2]
    message = ctx.message.content.split(' ', 3)[3]
    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()
    c.execute('UPDATE advetisement SET message = ? WHERE server_id = ? AND alias = ?', (message, ctx.guild.id, alias))
    conn.commit()
    conn.close()
    await ctx.response.send_message('Advertisement message has been set!', ephemeral=True)


async def advertise(ctx: discord.Interaction, alias):
    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()

    c.execute('SELECT message, image_url FROM advetisement WHERE server_id = ? AND alias = ?', (ctx.guild.id, alias))
    result = c.fetchone()
    conn.close()
    if result:
        if not result[0]:
            await ctx.response.send_message('No message set for this alias!', ephemeral=True)
            return
        title = result[0].split('\n')[0]
        body = result[0].split('\n', 1)[1]
        embed = discord.Embed(title=title, color=discord.Color.purple(), description=body)
        embed.set_image(url=result[1])
        await ctx.response.send_message(embed=embed)
    else:
        await ctx.response.send_message('This alias is not set up for advertisement!', ephemeral=True)


async def advertise_now(ctx: discord.Interaction, alias):
    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()
    c.execute('SELECT channel_id FROM advetisement WHERE server_id = ? AND alias = ?', (ctx.guild.id, alias))
    result = c.fetchone()
    conn.close()
    if result:
        await run_advertisement(result[0], ctx.client)
        await ctx.response.send_message(f'Advertisement has been sent into <#{result[0]}>!', ephemeral=True)
    else:
        await ctx.response.send_message('This alias is not set up for advertisement!', ephemeral=True)


async def add_image_to_advertisement(ctx: discord.Interaction, alias, image_url):
    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()
    c.execute('UPDATE advetisement SET image_url = ? WHERE server_id = ? AND alias = ?',
              (image_url, ctx.guild.id, alias))
    conn.commit()
    conn.close()
    await ctx.response.send_message('Image has been added to advertisement!', ephemeral=True)


async def advertisement_settings(ctx: discord.Interaction, alias):
    conn = sqlite3.connect('quantic.db')
    c = conn.cursor()
    c.execute('SELECT message, image_url, interval FROM advetisement WHERE alias = ? AND server_id = ?',
              (alias, ctx.guild.id))
    result = c.fetchone()
    conn.close()
    if not result:
        await ctx.response.send_message('This alias is not set up for advertisement!', ephemeral=True)
        return
    modal = AdvertisementSettingsModal(alias, result[0], result[1], result[2])
    await ctx.response.send_modal(modal)
