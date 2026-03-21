"""Bot minimal pour Dev Factory.

Ce bot sert d'exemple pour montrer comment gérer des commandes basiques et attribuer des rôles
sans passer par l'interface web.

Il utilise le token Discord du bot (DISCORD_BOT_TOKEN) et peut être lancé en parallèle du panel.
"""

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.environ.get("DISCORD_GUILD_ID", 0))

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=commands.DefaultHelpCommand(no_category="Commandes"),
)


@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user} ({bot.user.id})")
    if GUILD_ID:
        guild = bot.get_guild(GUILD_ID)
        if guild:
            print(f"Connecté au serveur : {guild.name} ({guild.id})")


@bot.command(name="ping")
async def ping(ctx: commands.Context):
    """Répond avec la latence du bot."""
    await ctx.reply(f"Pong ! Latence : {round(bot.latency*1000)}ms")


@bot.command(name="role")
@commands.has_permissions(manage_roles=True)
async def role(ctx: commands.Context, member: discord.Member, role: discord.Role):
    """Ajoute ou retire un rôle à un membre."""
    if role in member.roles:
        await member.remove_roles(role, reason="Gestion via Bot Dev Factory")
        await ctx.reply(f"Le rôle {role.name} a été retiré à {member.mention}.")
    else:
        await member.add_roles(role, reason="Gestion via Bot Dev Factory")
        await ctx.reply(f"Le rôle {role.name} a été attribué à {member.mention}.")


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise SystemExit("Veuillez configurer DISCORD_BOT_TOKEN dans backend/.env")

    bot.run(BOT_TOKEN)
