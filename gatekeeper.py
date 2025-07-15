import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from urllib.parse import quote
import asyncio

# Bot setup
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
GUILD_ID =

# Emojis (escaped)
EMOJI_CONTROLLER = "\U0001f3ae"  # ??
EMOJI_X = "\u274c"              # ?
EMOJI_CHECK = "\u2705"          # ?
EMOJI_GLOBE = "\U0001f310"      # ??

# Convert decimal XUID to Floodgate UUID
def decimal_to_floodgate_xuid(decimal_xuid: str) -> str:
    dec = int(decimal_xuid)
    hex_xuid = f"{dec:016X}"
    return f"00000000-0000-0000-{hex_xuid[:4]}-{hex_xuid[4:]}"

# /id command
@bot.tree.command(name="id", description="Get Floodgate ID for an Xbox user")
@app_commands.describe(user="Xbox gamertag (spaces are allowed)")
async def id(interaction: discord.Interaction, user: str):
    try:
        
        display_gamertag = user.strip()
        if not display_gamertag:
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    f"{EMOJI_X} Please enter a valid gamertag",
                    ephemeral=True
                )
            return

       
        try:
            await interaction.response.defer(thinking=True)
            deferred = True
        except discord.errors.NotFound:
            return
        except Exception as defer_error:
            print(f"Deferral error: {defer_error}")
            deferred = False

        
        try:
            api_gamertag = display_gamertag.replace(" ", "%20")
            url = f"https://playerdb.co/api/player/xbox/{api_gamertag}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        error_msg = f"{EMOJI_X} API Error (Status {response.status})"
                        await handle_response(interaction, deferred, error_msg)
                        return

                    data = await response.json()
                    
                    if not data.get("success", False):
                        error_msg = f"{EMOJI_X} Gamertag '{display_gamertag}' not found"
                        await handle_response(interaction, deferred, error_msg)
                        return

                  
                    floodgate_id = decimal_to_floodgate_xuid(data["data"]["player"]["id"])
                    embed = discord.Embed(
                        title=f"{EMOJI_CONTROLLER} Floodgate ID Lookup",
                        description=(
                            f"**Gamertag:** `{display_gamertag}`\n"
                            f"**Floodgate ID:** `{floodgate_id}`"
                        ),
                        color=discord.Color.blurple()
                    )
                   
                    
                    await handle_response(interaction, deferred, embed=embed)

        except asyncio.TimeoutError:
            await handle_response(interaction, deferred, f"{EMOJI_X} Request timed out. Try again later.")
        except Exception as e:
            print(f"Processing error: {type(e).__name__}: {str(e)}")
            await handle_response(interaction, deferred, f"{EMOJI_X} Service unavailable. Try again later.")

    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")
        await handle_error_response(interaction)

async def handle_response(interaction, deferred, message=None, embed=None, ephemeral=True):
    try:
        if deferred:
            if embed:
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(message, ephemeral=ephemeral)
        else:
            if not interaction.response.is_done():
                if embed:
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(message, ephemeral=ephemeral)
            else:
                await interaction.channel.send(embed=embed if embed else message)
    except Exception as e:
        print(f"Response handling error: {e}")
        try:
            await interaction.channel.send("An error occurred while processing your request.")
        except:
            pass

async def handle_error_response(interaction):
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                f"{EMOJI_X} Command failed. Please try again.",
                ephemeral=True
            )
    except:
        try:
            await interaction.channel.send(
                f"{EMOJI_X} Bot encountered an error processing your request."
            )
        except:
            pass
# Sync slash commands
@bot.event
async def on_ready():
    print(f"{EMOJI_CHECK} Logged in as {bot.user} (ID: {bot.user.id})")
    
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.custom, name="Gathering Floodgate IDs")
    )
    
    try:
        dev_guild = discord.Object(id=GUILD_ID)
        bot.tree.copy_global_to(guild=dev_guild)
        await bot.tree.sync(guild=dev_guild)
        print(f"{EMOJI_CHECK} Synced to dev guild {GUILD_ID}")

        await bot.tree.sync()
        print(f"{EMOJI_GLOBE} Synced globally!")
    except Exception as e:
        print(f"{EMOJI_X} Sync failed: {e}")

bot.run("Your Bot Token")
