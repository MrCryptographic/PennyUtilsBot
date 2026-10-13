import discord
from discord.ext import commands
from datetime import timedelta, datetime
import json
import os
import sys
import subprocess
import random
import asyncio
import traceback
import urllib.parse
import unicodedata
from functools import lru_cache
import yt_dlp
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from dotenv import load_dotenv

# Import our new modular AI Chat file
import ai_chat

# Load environment variables from .env file
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

BOT_VERSION = "2.9.0"
TOKEN = os.getenv("TOKEN")

# Default command prefix
DEFAULT_PREFIX = ";"

# Users who are allowed to execute moderation commands.
MODERATOR_IDS = {
    634734029094256650,
    1336521425858596896,
}

# Bot owner(s).
OWNER_IDS = {
    1336521425858596896,
}

# User ID that receives the automatic replies.
TARGET_USER_ID = 1069224942756966410

# Files used to store persistent data
DATA_FILE = "bot_data.json"
FAVORITES_FILE = "favorites.json"
PLAYLISTS_FILE = "playlists.json"


# ============================================================
# CUSTOM EMOJIS (IDs matched from screenshots)
# ============================================================
EMOJI_BLUSH = "<:blush:1541467236118692052>"
EMOJI_SMIRK = "<:smirk:1541467234986234007>"
EMOJI_SHY = "<:shy:1541467234092974170>"
EMOJI_LOVE = "<:love:1541467233161576581>"
EMOJI_SHOCKED = "<:shocked:1541467232012472401>"
EMOJI_PURPLE = "<a:purple:1542171234794733578>"
EMOJI_PIZZA = "<:pizza:1542171232898908260>"
EMOJI_DANCING = "<a:dancing:1542171231418196068>"
EMOJI_KISS_NEW = "<:kiss:1542171226754261083>"
EMOJI_SMILE = "<:smile:1542171225399500830>"
EMOJI_BOYKISSER = "<:boykisser:1542171223767654441>"
EMOJI_BOYKISSER_HAPPY = "<:boykisser_happy:1542171222400438312>"
EMOJI_BOYKISSER_SMOKING = "<:boykisser_smoking:1542171221326700666>"
EMOJI_BOYKISSER_EAT = "<:boykisser_eat:1542171220454146079>"
EMOJI_BOYKISSER_BOOP = "<a:boykisser_boop:1542171219640582144>"
EMOJI_BOYKISSER_RIGHT = "<:boykisser_right:1542171218663309362>"
EMOJI_BOYKISSER_SEE = "<a:boykisser_see:1542171206042525856>"
EMOJI_BOYKISSER_HUH = "<:boykisser_huh:1542171195183599728>"


# ============================================================
# PERSISTENT DATA MANAGEMENT
# ============================================================

def load_data():
    default_data = {
        "prefixes": {},
        "warnings": {},
        "logs": {},
        "devtest": {},
        "blacklist": {"all": []},
        "disabled_commands": {"global": [], "guilds": {}},
        "personas": {}, 
        "auto_replies": [
            f"Oh, look who it is! {EMOJI_SMIRK}",
            f"H-hey! {EMOJI_SHY}",
            f"Sending some love your way! {EMOJI_LOVE}",
            f"Do you want some pizza? {EMOJI_PIZZA}",
            f"I see you... {EMOJI_BOYKISSER_SEE}"
        ],
        "reply_cooldown": 10
    }

    if not os.path.exists(DATA_FILE):
        return default_data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if "blacklist" in loaded and isinstance(loaded["blacklist"], list):
                loaded["blacklist"] = {"all": loaded["blacklist"]}
            for key, val in default_data.items():
                if key not in loaded:
                    loaded[key] = val
            return loaded
    except Exception:
        return default_data


data = load_data()


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_favorites():
    default_favs = {"guilds": {}, "users": {}}
    if not os.path.exists(FAVORITES_FILE):
        return default_favs
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if "guilds" not in loaded:
                loaded["guilds"] = {}
            if "users" not in loaded:
                loaded["users"] = {}
            return loaded
    except Exception:
        return default_favs


favorites_data = load_favorites()


def save_favorites():
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favorites_data, f, indent=4)


def load_playlists():
    default_pls = {"guilds": {}, "users": {}}
    if not os.path.exists(PLAYLISTS_FILE):
        return default_pls
    try:
        with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)
            if "guilds" not in loaded:
                loaded["guilds"] = {}
            if "users" not in loaded:
                loaded["users"] = {}
            return loaded
    except Exception:
        return default_pls


playlists_data = load_playlists()


def save_playlists():
    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
        json.dump(playlists_data, f, indent=4)


def get_prefix(bot, message):
    return data["prefixes"].get(
        str(message.guild.id) if message.guild else "dm",
        DEFAULT_PREFIX
    )


def sanitize_markdown(text: str, max_len: int = 50) -> str:
    if not text:
        return "Unknown Track"
    cleaned = text.replace("[", "(").replace("]", ")").replace("\n", " ").strip()
    if len(cleaned) > max_len:
        return cleaned[:max_len - 3] + "..."
    return cleaned


def get_meme_font(size: int, script_dir: str):
    candidates = [
        os.path.join(script_dir, "impact.ttf"),
        os.path.join(script_dir, "Impact.ttf"),
        os.path.join(script_dir, "assets", "impact.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "impact.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "Impact.ttf"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts", "arialbd.ttf"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


@lru_cache(maxsize=32)
def _load_meme_font(path: str, size: int):
    return ImageFont.truetype(path, size)


@lru_cache(maxsize=8192)
def _font_supports_meme_character(path: str, size: int, character: str) -> bool:
    try:
        font = _load_meme_font(path, size)
        glyph = font.getmask(character)
        missing_glyph = font.getmask("\U0010ffff")
        return glyph.size != missing_glyph.size or bytes(glyph) != bytes(missing_glyph)
    except (OSError, ValueError):
        return False


def _meme_fallback_font_paths(script_dir: str):
    windows_fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    candidates = [
        os.path.join(windows_fonts, "segoeui.ttf"),
        os.path.join(windows_fonts, "arial.ttf"),
        os.path.join(windows_fonts, "tahoma.ttf"),
        os.path.join(windows_fonts, "simsun.ttc"),
        os.path.join(windows_fonts, "seguiemj.ttf"),
    ]
    paths = []
    primary = get_meme_font(16, script_dir)
    primary_path = getattr(primary, "path", None)
    if isinstance(primary_path, str):
        paths.append(primary_path)
    paths.extend(path for path in candidates if os.path.isfile(path))
    return list(dict.fromkeys(paths))


def _is_meme_emoji(character: str) -> bool:
    codepoint = ord(character)
    return (
        0x1F000 <= codepoint <= 0x1FAFF
        or 0x2600 <= codepoint <= 0x27BF
        or 0x2300 <= codepoint <= 0x23FF
        or 0x1F1E6 <= codepoint <= 0x1F1FF
        or codepoint in (0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D, 0x3297, 0x3299)
    )


@lru_cache(maxsize=1)
def _arabic_presentation_forms():
    forms = {}
    for codepoint in (*range(0xFB50, 0xFE00), *range(0xFE70, 0xFF00)):
        character = chr(codepoint)
        name = unicodedata.name(character, "")
        if "ARABIC LETTER" not in name:
            continue
        normalized = unicodedata.normalize("NFKC", character)
        if len(normalized) != 1:
            continue

        form_name = next(
            (form for form in ("ISOLATED", "FINAL", "INITIAL", "MEDIAL") if name.endswith(f"{form} FORM")),
            None
        )
        if form_name:
            forms.setdefault(normalized, {})[form_name.lower()] = character
    return forms


def _shape_arabic_for_basic_pillow(text: str) -> str:
    forms = _arabic_presentation_forms()
    shaped = list(text)
    arabic_indexes = [
        index for index, character in enumerate(text)
        if unicodedata.bidirectional(character) in ("R", "AL")
    ]
    for index in arabic_indexes:
        character_forms = forms.get(text[index])
        if not character_forms:
            continue

        previous_index = index - 1
        while previous_index >= 0 and unicodedata.category(text[previous_index]) in ("Mn", "Mc", "Me"):
            previous_index -= 1
        next_index = index + 1
        while next_index < len(text) and unicodedata.category(text[next_index]) in ("Mn", "Mc", "Me"):
            next_index += 1

        previous_forms = forms.get(text[previous_index], {}) if previous_index >= 0 else {}
        next_forms = forms.get(text[next_index], {}) if next_index < len(text) else {}
        joins_previous = "initial" in previous_forms and "final" in character_forms
        joins_next = "initial" in character_forms and "final" in next_forms

        if joins_previous and joins_next:
            form = "medial"
        elif joins_previous:
            form = "final"
        elif joins_next:
            form = "initial"
        else:
            form = "isolated"
        shaped[index] = character_forms.get(form, character_forms.get("isolated", text[index]))

    if not arabic_indexes:
        return text

    start = arabic_indexes[0]
    end = arabic_indexes[-1] + 1
    rtl_segment = shaped[start:end]
    return "".join(shaped[:start] + list(reversed(rtl_segment)) + shaped[end:])


def _meme_font_for_character(character: str, primary_font, fallback_paths: list[str]):
    primary_path = getattr(primary_font, "path", None)
    size = getattr(primary_font, "size", 28)
    if isinstance(primary_path, bytes):
        primary_path = os.fsdecode(primary_path)
    if isinstance(primary_path, str) and _font_supports_meme_character(primary_path, size, character):
        return primary_font, False, True

    emoji_character = _is_meme_emoji(character)
    for path in fallback_paths:
        if path == primary_path:
            continue
        is_emoji_font = os.path.basename(path).lower() == "seguiemj.ttf"
        if emoji_character and not is_emoji_font:
            continue
        if not emoji_character and is_emoji_font:
            continue
        if _font_supports_meme_character(path, size, character):
            try:
                return _load_meme_font(path, size), is_emoji_font, True
            except (OSError, ValueError):
                continue
    return primary_font, False, False


def _meme_text_runs(text: str, primary_font, script_dir: str):
    fallback_paths = _meme_fallback_font_paths(script_dir)
    runs = []
    previous_font = primary_font
    previous_emoji = False
    for character in text:
        if unicodedata.category(character) in ("Cf", "Mn", "Mc", "Me") or (
            character.isspace() and previous_font is not primary_font
        ):
            font, is_emoji = previous_font, previous_emoji
            supported = True
        else:
            font, is_emoji, supported = _meme_font_for_character(character, primary_font, fallback_paths)
            previous_font, previous_emoji = font, is_emoji
        if not supported:
            character = "?"

        if runs and runs[-1][1] is font and runs[-1][2] == is_emoji:
            runs[-1] = (runs[-1][0] + character, font, is_emoji)
        else:
            runs.append((character, font, is_emoji))
    return runs


def _meme_text_width(text: str, primary_font, script_dir: str) -> float:
    width = 0
    for run, font, _ in _meme_text_runs(text, primary_font, script_dir):
        width += font.getlength(run) if hasattr(font, "getlength") else len(run) * getattr(font, "size", 16)
    return width


def _draw_meme_text(draw, position, text: str, fill, primary_font, script_dir: str):
    x, y = position
    for run, font, is_emoji in _meme_text_runs(text, primary_font, script_dir):
        run = _shape_arabic_for_basic_pillow(run)
        draw.text((x, y), run, fill=fill, font=font, embedded_color=is_emoji)
        x += font.getlength(run) if hasattr(font, "getlength") else len(run) * getattr(font, "size", 16)


def _wrap_meme_text(text: str, max_width: int, primary_font, script_dir: str) -> list[str]:
    lines = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if not line or _meme_text_width(candidate, primary_font, script_dir) <= max_width:
                if _meme_text_width(candidate, primary_font, script_dir) <= max_width:
                    line = candidate
                    continue
            if line:
                lines.append(line)
                line = ""

            if _meme_text_width(word, primary_font, script_dir) <= max_width:
                line = word
                continue

            part = ""
            for character in word:
                candidate_part = part + character
                if part and _meme_text_width(candidate_part, primary_font, script_dir) > max_width:
                    lines.append(part)
                    part = character
                else:
                    part = candidate_part
            line = part
        if line:
            lines.append(line)
    return lines or [""]


# ============================================================
# BOT SETUP
# ============================================================

intents = discord.Intents.all()

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None
)

last_reply_time = {}
user_spam_tracker = {}


# ============================================================
# PERMISSION CHECKS & GLOBAL LOCKS
# ============================================================

def is_moderator(user_id):
    return user_id in MODERATOR_IDS or user_id in OWNER_IDS


def is_owner(user_id):
    return user_id in OWNER_IDS


def moderator_only():
    async def predicate(ctx):
        if not is_moderator(ctx.author.id):
            raise commands.CheckFailure("You are not authorized to use moderation commands.")
        return True
    return commands.check(predicate)


def owner_only():
    async def predicate(ctx):
        if not is_owner(ctx.author.id):
            raise commands.CheckFailure("OWNER_ONLY")
        return True
    return commands.check(predicate)


@bot.check
async def blacklist_check(ctx):
    uid = ctx.author.id
    bl = data.get("blacklist", {})
    if uid in bl.get("all", []):
        raise commands.CheckFailure("BLACKLISTED")
    if ctx.command and uid in bl.get(ctx.command.name, []):
        raise commands.CheckFailure("BLACKLISTED")
    return True


@bot.check
async def disabled_command_check(ctx):
    if not ctx.command:
        return True
    cmd_name = ctx.command.name
    disabled = data.get("disabled_commands", {"global": [], "guilds": {}})
    if cmd_name in disabled.get("global", []):
        raise commands.CheckFailure(f"DISABLED_GLOBAL:{cmd_name}")
    if ctx.guild and cmd_name in disabled.get("guilds", {}).get(str(ctx.guild.id), []):
        raise commands.CheckFailure(f"DISABLED_SERVER:{cmd_name}")
    return True


@bot.check
async def anti_spam_check(ctx):
    if is_moderator(ctx.author.id):
        return True
    if not ctx.guild:
        return True

    now = datetime.now()
    user_id = ctx.author.id
    SPAM_COOLDOWN = 3.0

    if user_id not in user_spam_tracker:
        user_spam_tracker[user_id] = {"last_cmd": now, "warnings": 0}
        return True

    tracker = user_spam_tracker[user_id]
    time_diff = (now - tracker["last_cmd"]).total_seconds()

    if time_diff < SPAM_COOLDOWN:
        tracker["warnings"] += 1
        tracker["last_cmd"] = now

        if tracker["warnings"] >= 3:
            tracker["warnings"] = 0
            if ctx.guild.me.guild_permissions.moderate_members and ctx.author.top_role < ctx.guild.me.top_role:
                until = discord.utils.utcnow() + timedelta(minutes=1)
                try:
                    await ctx.author.timeout(until, reason="Command spamming")
                    await ctx.send(f"⏳ {ctx.author.mention} has been timed out for 1 minute due to command spamming.")
                except Exception:
                    pass
            else:
                await ctx.send(f"⚠️ {ctx.author.mention}, you have hit the spam threshold! Slow down.", delete_after=5)
            raise commands.CheckFailure("SPAMMING")
        else:
            await ctx.send(f"⚠️ {ctx.author.mention}, you're using commands too fast! Slow down. ({tracker['warnings']}/3 warnings)", delete_after=5)
            raise commands.CheckFailure("SPAMMING")
    else:
        tracker["last_cmd"] = now
        tracker["warnings"] = max(0, tracker["warnings"] - 1)
        return True


@bot.check
async def devtest_lock_check(ctx):
    if not ctx.guild:
        return True

    guild_id_str = str(ctx.guild.id)
    locked_channel_id = data.get("devtest", {}).get(guild_id_str)

    if locked_channel_id:
        channel = ctx.guild.get_channel(locked_channel_id)
        if channel is None:
            del data["devtest"][guild_id_str]
            save_data()
            return True

        if ctx.command and ctx.command.name == "undevtest":
            return True

        if ctx.channel.id != locked_channel_id:
            raise commands.CheckFailure(f"DEVTEST_LOCKED:{locked_channel_id}")

    return True


# ============================================================
# LOGGING
# ============================================================

purge_log_suppression = set()

async def log_action(
    guild,
    title: str,
    *,
    actor=None,
    target=None,
    details=None,
    color=discord.Color.orange(),
    timestamp=None
):
    channel_id = data["logs"].get(str(guild.id))
    if not channel_id:
        return

    channel = guild.get_channel(channel_id)
    if not channel:
        return

    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=timestamp or discord.utils.utcnow()
    )
    if actor is not None:
        embed.add_field(name="Moderator / Actor", value=f"{actor.mention} (`{actor}` · `{actor.id}`)", inline=False)
    if target is not None:
        embed.add_field(name="Target", value=f"{target.mention} (`{target}` · `{target.id}`)", inline=False)
    for name, value in (details or {}).items():
        value = str(value)
        if len(value) > 1024:
            value = value[:1021] + "..."
        embed.add_field(name=name, value=value or "—", inline=False)
    embed.set_footer(text=f"{guild.name} • Moderation & message logs")

    try:
        await channel.send(embed=embed)
    except (discord.Forbidden, discord.HTTPException) as error:
        print(f"[Log Delivery Error in {guild}]: {error}")


async def find_message_delete_actor(guild, *, target_id=None, channel_id, bulk=False, count=None):
    audit_action = (
        discord.AuditLogAction.message_bulk_delete
        if bulk else discord.AuditLogAction.message_delete
    )
    cutoff = discord.utils.utcnow() - timedelta(seconds=10)
    for attempt in range(2):
        try:
            async for entry in guild.audit_logs(limit=10, action=audit_action):
                if entry.created_at < cutoff:
                    continue
                extra_channel = getattr(getattr(entry, "extra", None), "channel", None)
                if not extra_channel or extra_channel.id != channel_id:
                    continue
                if bulk:
                    entry_count = getattr(entry.extra, "count", None)
                    if count is not None and entry_count != count:
                        continue
                elif target_id is not None:
                    entry_target_id = getattr(entry.target, "id", None)
                    if entry_target_id != target_id:
                        continue
                return entry.user
        except (discord.Forbidden, discord.HTTPException) as error:
            print(f"[Audit Log Lookup Error in {guild}]: {error}")
            return None
        if attempt == 0:
            await asyncio.sleep(0.5)
    return None


def format_deleted_message(message):
    content = message.content or "[no text content]"
    attachments = ", ".join(attachment.filename for attachment in message.attachments)
    if attachments:
        content += f" [Attachments: {attachments}]"
    return f"{message.author} (`{message.author.id}`): {content}"


# ============================================================
# AI CHATBOT SYSTEM (LM STUDIO INTEGRATION)
# ============================================================

user_chat_history = {}

@bot.command()
async def persona(ctx, name: str = None):
    if not name:
        available = ", ".join([f"`{p}`" for p in ai_chat.PERSONALITIES.keys()])
        await ctx.send(
            f"**Available AI Personas:** {available}\n"
            f"**Usage:** `{get_prefix(bot, ctx.message)}persona <name>`"
        )
        return

    name = name.lower()
    if name not in ai_chat.PERSONALITIES:
        await ctx.send(f"Unknown persona! {EMOJI_BOYKISSER_HUH}")
        return

    data["personas"][str(ctx.author.id)] = name
    save_data()
    user_chat_history.pop(ctx.author.id, None)
    await ctx.send(f"Your AI persona has been updated to **{name}**. Conversation history cleared! {EMOJI_BLUSH}")

@bot.command()
async def clearchat(ctx):
    user_chat_history.pop(ctx.author.id, None)
    await ctx.send(f"Your chat history has been wiped! Amnesia time! {EMOJI_SHOCKED}")

@bot.command(aliases=["c", "ai"])
async def chat(ctx, *, message: str = None):
    if not message:
        await ctx.send(f"What do you want to say to me? {EMOJI_BOYKISSER_HUH}")
        return

    user_id = ctx.author.id
    persona_name = data.get("personas", {}).get(str(user_id), "default")

    if user_id not in user_chat_history:
        user_chat_history[user_id] = []

    history = user_chat_history[user_id][-10:]

    if persona_name == "superuncensored" and not history:
        await ctx.send(
            "⚠️ **Content warning:** The `superuncensored` persona may use strong "
            "language or generate offensive and inappropriate content. It is "
            "not suitable for all audiences."
        )

    async with ctx.typing():
        response = await ai_chat.generate_response(message, persona=persona_name, history=history)

        user_chat_history[user_id].append({"role": "user", "content": message})
        user_chat_history[user_id].append({"role": "assistant", "content": response})

        if len(response) > 1990:
            chunks = [response[i:i+1990] for i in range(0, len(response), 1990)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)


# ============================================================
# MUSIC ENGINE: YT-DLP, QUEUE, FILTERS & VC STATUS
# ============================================================

YTDL_OPTS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios', 'web_creator']
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
}

EFFECT_FILTERS = {
    "none": None,
    "reverb": "aecho=0.8:0.88:60:0.4",
    "bassboost": "bass=g=10:f=110:w=0.6",
    "superbassboost": "bass=g=20:f=110:w=0.6",
    "very_loud": "acrusher=level_in=8:level_out=18:bits=8:mode=log,volume=-24dB",
    "nightcore": "asetrate=48000*1.25,aresample=48000",
    "vaporwave": "asetrate=48000*0.8,aresample=48000",
    "8d": "apulsator=hz=0.125",
    "echo": "aecho=0.8:0.9:1000:0.3"
}

music_states = {}

def get_music_state(guild_id: int):
    if guild_id not in music_states:
        music_states[guild_id] = {
            "queue": [],
            "history": [],
            "current": None,
            "effect": "none",
            "volume": 0.5,
            "loop": False,
            "autoplay": False,
            "autorestart_on_effect": True,
            "disconnect_task": None,
            "text_channel": None
        }
    return music_states[guild_id]

def get_ffmpeg_options(effect_name: str = None):
    options = "-vn"
    if effect_name and effect_name in EFFECT_FILTERS and EFFECT_FILTERS[effect_name]:
        options += f" -af {EFFECT_FILTERS[effect_name]}"
    return {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -user_agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"',
        'options': options
    }

async def update_vc_status(channel, status_text: str = None):
    if not channel:
        return
    try:
        trimmed = status_text[:490] if status_text else None
        if hasattr(channel, "set_status"):
            await channel.set_status(trimmed)
        elif hasattr(channel, "edit"):
            try:
                await channel.edit(status=trimmed)
            except (TypeError, discord.HTTPException):
                await channel._state.http.set_voice_channel_status(channel.id, trimmed)
    except Exception:
        pass

async def schedule_disconnect(guild_id: int, delay: int = 180):
    state = get_music_state(guild_id)
    if state["disconnect_task"] and not state["disconnect_task"].done():
        state["disconnect_task"].cancel()

    async def _disconnect_timer():
        try:
            await asyncio.sleep(delay)
            guild = bot.get_guild(guild_id)
            if guild and guild.voice_client:
                vc = guild.voice_client
                if not vc.is_playing() and not vc.is_paused():
                    await update_vc_status(vc.channel, None)
                    await vc.disconnect()
                    if state["text_channel"]:
                        await state["text_channel"].send(f"Disconnected from voice channel due to inactivity. {EMOJI_BOYKISSER_SMOKING}")
                    music_states.pop(guild_id, None)
        except asyncio.CancelledError:
            pass

    state["disconnect_task"] = asyncio.create_task(_disconnect_timer())

def cancel_disconnect(guild_id: int):
    state = get_music_state(guild_id)
    if state["disconnect_task"] and not state["disconnect_task"].done():
        state["disconnect_task"].cancel()
    state["disconnect_task"] = None

async def resolve_stream(track_dict: dict):
    target_url = track_dict.get('webpage_url') or track_dict.get('url')
    
    if target_url and (track_dict.get("is_attachment") or "videoplayback" in target_url):
        return target_url

    loop = asyncio.get_event_loop()
    def _extract():
        with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
            return ydl.extract_info(target_url, download=False)
    
    try:
        data_info = await loop.run_in_executor(None, _extract)
    except Exception as e:
        print(f"[Extractor Error]: {e}")
        return None

    if not data_info:
        return None

    if data_info.get('url'):
        return data_info['url']

    if 'formats' in data_info:
        audio_formats = [f for f in data_info['formats'] if f.get('acodec') != 'none' and f.get('url')]
        if audio_formats:
            audio_only = [f for f in audio_formats if f.get('vcodec') == 'none']
            return audio_only[-1]['url'] if audio_only else audio_formats[-1]['url']

    return None

async def play_next_track(guild_id: int):
    state = get_music_state(guild_id)
    guild = bot.get_guild(guild_id)
    if not guild or not guild.voice_client:
        return

    vc = guild.voice_client

    if state["loop"] and state["current"]:
        track = state["current"]
    elif state["queue"]:
        track = state["queue"].pop(0)
        state["current"] = track
        state["history"].append(track)
    elif state.get("autoplay") and state["history"]:
        # Youtube Autoplay logic using RD Mix playlist
        last_url = state["history"][-1].get("webpage_url", "")
        
        parsed = urllib.parse.urlparse(last_url)
        vid_id = None
        if parsed.hostname in ['www.youtube.com', 'youtube.com', 'm.youtube.com']:
            qs = urllib.parse.parse_qs(parsed.query)
            if 'v' in qs:
                vid_id = qs['v'][0]
        elif parsed.hostname == 'youtu.be':
            vid_id = parsed.path.lstrip('/')

        track = None
        if vid_id:
            mix_url = f"https://www.youtube.com/watch?v={vid_id}&list=RD{vid_id}"
            loop_ev = asyncio.get_event_loop()
            def _get_mix():
                with yt_dlp.YoutubeDL({'extract_flat': True, 'quiet': True, 'no_warnings': True}) as ydl:
                    return ydl.extract_info(mix_url, download=False)
            try:
                mix_info = await loop_ev.run_in_executor(None, _get_mix)
                if mix_info and 'entries' in mix_info:
                    for entry in mix_info['entries']:
                        if entry and entry.get('id'):
                            url_check = f"https://www.youtube.com/watch?v={entry['id']}"
                            # Pick a related song that wasn't recently played
                            if not any(t.get('webpage_url') == url_check for t in state["history"][-15:]):
                                track = {
                                    'title': sanitize_markdown(entry.get('title', 'Autoplay Track'), max_len=60),
                                    'webpage_url': url_check
                                }
                                state["current"] = track
                                state["history"].append(track)
                                if state["text_channel"]:
                                    await state["text_channel"].send(f"📻 **Autoplay** queued related track: **{track['title']}** {EMOJI_BLUSH}")
                                break
            except Exception as e:
                print(f"[Autoplay Error]: {e}")

        if not track:
            state["current"] = None
            await update_vc_status(vc.channel, None)
            await schedule_disconnect(guild_id, delay=180)
            return
    else:
        state["current"] = None
        await update_vc_status(vc.channel, None)
        await schedule_disconnect(guild_id, delay=180)
        return

    # Cap history to 50 items
    if len(state["history"]) > 50:
        state["history"].pop(0)

    cancel_disconnect(guild_id)

    try:
        stream_url = await resolve_stream(track)
        if not stream_url:
            if state["text_channel"]:
                await state["text_channel"].send(f"Could not load audio for **{track['title']}**. Skipping... {EMOJI_SHOCKED}")
            await play_next_track(guild_id)
            return

        ffmpeg_opts = get_ffmpeg_options(state["effect"])
        source = discord.FFmpegPCMAudio(stream_url, **ffmpeg_opts)
        transformed = discord.PCMVolumeTransformer(source, volume=state["volume"])

        def after_callback(err):
            if err:
                print(f"Playback error: {err}")
            asyncio.run_coroutine_threadsafe(play_next_track(guild_id), bot.loop)

        vc.play(transformed, after=after_callback)

        clean_title = sanitize_markdown(track["title"], max_len=60)
        if vc.channel:
            await update_vc_status(vc.channel, f"🎶 {clean_title}")

        if state["text_channel"]:
            fx_note = f" (Effect: `{state['effect']}`)" if state["effect"] != "none" else ""
            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"[{clean_title}]({track['webpage_url']}){fx_note}",
                color=discord.Color.purple()
            )
            view = NowPlayingView(guild_id)
            await state["text_channel"].send(embed=embed, view=view)

    except Exception as e:
        if state["text_channel"]:
            await state["text_channel"].send(f"Error starting playback: `{e}`")
        await play_next_track(guild_id)


# ============================================================
# INTERACTIVE MUSIC VIEWS
# ============================================================

class EffectSelectView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=90)
        self.guild_id = guild_id
        state = get_music_state(guild_id)
        current = state["effect"]

        options = [
            discord.SelectOption(label="None", value="none", description="Normal playback without filters", emoji="🎵", default=(current == "none")),
            discord.SelectOption(label="Reverb", value="reverb", description="Ambient spacious reverb", emoji="🌌", default=(current == "reverb")),
            discord.SelectOption(label="Bassboost", value="bassboost", description="Punchy low-end bass filter", emoji="🔉", default=(current == "bassboost")),
            discord.SelectOption(label="Super Bassboost", value="superbassboost", description="Extra-strong low-end bass boost", emoji="🔊", default=(current == "superbassboost")),
            discord.SelectOption(label="VERY LOUD", value="very_loud", description="Crunchy, reduced-level distortion", emoji="📢", default=(current == "very_loud")),
            discord.SelectOption(label="Nightcore", value="nightcore", description="Sped up with raised pitch", emoji="⚡", default=(current == "nightcore")),
            discord.SelectOption(label="Vaporwave", value="vaporwave", description="Slowed down with deeper pitch", emoji="🌆", default=(current == "vaporwave")),
            discord.SelectOption(label="8D Audio", value="8d", description="Dynamic ear-to-ear panning", emoji="🎧", default=(current == "8d")),
            discord.SelectOption(label="Echo", value="echo", description="Distinct delayed audio echo", emoji="🗣️", default=(current == "echo"))
        ]

        select = discord.ui.Select(placeholder="Select an audio effect...", options=options)
        select.callback = self.select_callback
        self.add_item(select)

        ar_status = "ON" if state["autorestart_on_effect"] else "OFF"
        btn_style = discord.ButtonStyle.success if state["autorestart_on_effect"] else discord.ButtonStyle.secondary
        self.toggle_btn = discord.ui.Button(label=f"Auto-Restart on Effect: {ar_status}", style=btn_style, row=1)
        self.toggle_btn.callback = self.toggle_autorestart
        self.add_item(self.toggle_btn)

    async def toggle_autorestart(self, interaction: discord.Interaction):
        state = get_music_state(self.guild_id)
        state["autorestart_on_effect"] = not state["autorestart_on_effect"]
        await interaction.response.edit_message(view=EffectSelectView(self.guild_id))

    async def select_callback(self, interaction: discord.Interaction):
        chosen = interaction.data["values"][0]
        state = get_music_state(self.guild_id)
        state["effect"] = chosen

        restarted_note = ""
        guild = bot.get_guild(self.guild_id)
        vc = guild.voice_client if guild else None

        if state["autorestart_on_effect"] and vc and (vc.is_playing() or vc.is_paused()) and state["current"]:
            current_track = state["current"]
            state["queue"].insert(0, current_track)
            state["current"] = None
            vc.stop()
            restarted_note = "\n*(Track automatically restarted with new effect applied)*"

        embed = discord.Embed(
            title="🎛️ Audio Effects",
            description=f"Active effect set to: **`{chosen}`**!{restarted_note}",
            color=discord.Color.purple()
        )
        await interaction.response.edit_message(embed=embed, view=EffectSelectView(self.guild_id))


class NowPlayingView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id

    @discord.ui.button(label="⏯️", style=discord.ButtonStyle.secondary)
    async def pause_resume_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(self.guild_id)
        vc = guild.voice_client if guild else None
        if not vc:
            await interaction.response.send_message("I am not connected to voice!", ephemeral=True)
            return

        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("Paused playback! ⏸️", ephemeral=True)
        elif vc.is_paused():
            vc.resume()
            await interaction.response.send_message("Resumed playback! ▶️", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing is currently active!", ephemeral=True)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.secondary)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(self.guild_id)
        vc = guild.voice_client if guild else None
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message("Skipped track! ⏭️", ephemeral=True)
        else:
            await interaction.response.send_message("Nothing to skip!", ephemeral=True)

    @discord.ui.button(label="🔂", style=discord.ButtonStyle.secondary)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_music_state(self.guild_id)
        state["loop"] = not state["loop"]
        status = "enabled" if state["loop"] else "disabled"
        await interaction.response.send_message(f"Loop is now **{status}**! 🔂", ephemeral=True)

    @discord.ui.button(label="📻 Autoplay", style=discord.ButtonStyle.secondary)
    async def autoplay_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_music_state(self.guild_id)
        state["autoplay"] = not state.get("autoplay", False)
        status = "enabled" if state["autoplay"] else "disabled"
        await interaction.response.send_message(f"Autoplay is now **{status}**! 📻", ephemeral=True)

    @discord.ui.button(label="❤️", style=discord.ButtonStyle.success)
    async def fav_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_music_state(self.guild_id)
        if not state["current"]:
            await interaction.response.send_message("No song is currently playing to favorite!", ephemeral=True)
            return

        track = state["current"]
        guild_id_str = str(self.guild_id)
        user_id_str = str(interaction.user.id)

        clean_title = sanitize_markdown(track["title"], max_len=80)
        fav_item_guild = {
            "title": clean_title,
            "url": track["webpage_url"],
            "user_id": interaction.user.id,
            "user_name": str(interaction.user),
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        fav_item_user = {
            "title": clean_title,
            "url": track["webpage_url"],
            "guild_id": self.guild_id,
            "guild_name": interaction.guild.name if interaction.guild else "Direct",
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        g_list = favorites_data["guilds"].setdefault(guild_id_str, [])
        if not any(item["url"] == track["webpage_url"] for item in g_list):
            g_list.append(fav_item_guild)

        u_list = favorites_data["users"].setdefault(user_id_str, [])
        if not any(item["url"] == track["webpage_url"] for item in u_list):
            u_list.append(fav_item_user)

        save_favorites()
        await interaction.response.send_message(f"Added **{clean_title}** to your favorites! ❤️", ephemeral=True)

    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_music_state(self.guild_id)
        state["queue"].clear()
        state["current"] = None
        state["loop"] = False

        guild = bot.get_guild(self.guild_id)
        vc = guild.voice_client if guild else None
        if vc:
            await update_vc_status(vc.channel, None)
            if vc.is_playing() or vc.is_paused():
                vc.stop()

        await interaction.response.send_message("Stopped playback and cleared queue! ⏹️", ephemeral=True)


class InteractiveQueueView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.guild_id = guild_id
        self.page = 0
        self.update_buttons()

    def get_embed(self):
        state = get_music_state(self.guild_id)
        embed = discord.Embed(title="🎶 Music Queue", color=discord.Color.purple())

        if state["current"]:
            loop_txt = " (Looping)" if state["loop"] else ""
            clean_np = sanitize_markdown(state["current"].get("title", "Unknown Track"), max_len=55)
            embed.add_field(
                name="Now Playing",
                value=f"[{clean_np}]({state['current'].get('webpage_url', '')}){loop_txt}"[:1000],
                inline=False
            )

        if not state["queue"]:
            embed.add_field(name="Up Next", value="No upcoming tracks in queue.", inline=False)
            return embed

        items_per_page = 6
        total_pages = max(1, (len(state["queue"]) + items_per_page - 1) // items_per_page)
        self.page = min(self.page, total_pages - 1)

        start = self.page * items_per_page
        end = start + items_per_page
        current_slice = state["queue"][start:end]

        queue_txt = ""
        for idx, track in enumerate(current_slice, start + 1):
            clean_title = sanitize_markdown(track.get("title", "Unknown Track"), max_len=45)
            line = f"`{idx}.` [{clean_title}]({track.get('webpage_url', '')})\n"
            if len(queue_txt) + len(line) < 950:
                queue_txt += line

        embed.add_field(name="Up Next", value=queue_txt if queue_txt else "No songs.", inline=False)
        embed.set_footer(text=f"Page {self.page + 1} of {total_pages} • Total queued: {len(state['queue'])}")
        return embed

    def update_buttons(self):
        state = get_music_state(self.guild_id)
        items_per_page = 6
        total_pages = max(1, (len(state["queue"]) + items_per_page - 1) // items_per_page)

        self.prev_btn.disabled = (self.page <= 0)
        self.next_btn.disabled = (self.page >= total_pages - 1)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_music_state(self.guild_id)
        total_pages = max(1, (len(state["queue"]) + 5) // 6)
        if self.page < total_pages - 1:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="⏯️", style=discord.ButtonStyle.primary)
    async def toggle_pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(self.guild_id)
        vc = guild.voice_client if guild else None
        if vc and vc.is_playing():
            vc.pause()
        elif vc and vc.is_paused():
            vc.resume()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="⏭️ Skip", style=discord.ButtonStyle.primary)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = bot.get_guild(self.guild_id)
        vc = guild.voice_client if guild else None
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
        await asyncio.sleep(0.5)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="🔀 Shuffle", style=discord.ButtonStyle.secondary)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_music_state(self.guild_id)
        if len(state["queue"]) > 1:
            random.shuffle(state["queue"])
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="🗑️ Clear", style=discord.ButtonStyle.danger)
    async def clear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = get_music_state(self.guild_id)
        state["queue"].clear()
        self.page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)


class FavoritesView(discord.ui.View):
    def __init__(self, ctx, mode: str = "guild"):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.mode = mode
        self.page = 0
        self.rebuild_ui()

    def get_list(self):
        if self.mode == "guild":
            return favorites_data["guilds"].get(str(self.ctx.guild.id), [])
        else:
            return favorites_data["users"].get(str(self.ctx.author.id), [])

    def rebuild_ui(self):
        self.clear_items()
        fav_list = self.get_list()
        items_per_page = 6
        total_pages = max(1, (len(fav_list) + items_per_page - 1) // items_per_page)
        self.page = min(self.page, total_pages - 1)

        toggle_label = "Switch to My Favorites 👤" if self.mode == "guild" else "Switch to Server Favorites 🌐"
        toggle_btn = discord.ui.Button(label=toggle_label, style=discord.ButtonStyle.primary, row=0)
        toggle_btn.callback = self.toggle_mode
        self.add_item(toggle_btn)

        play_all_btn = discord.ui.Button(label="▶️ Play All Favs", style=discord.ButtonStyle.success, row=0, disabled=(len(fav_list) == 0))
        play_all_btn.callback = self.play_all_favs
        self.add_item(play_all_btn)

        prev_btn = discord.ui.Button(label="◀ Prev", style=discord.ButtonStyle.secondary, row=1, disabled=(self.page <= 0))
        prev_btn.callback = self.prev_page
        self.add_item(prev_btn)

        next_btn = discord.ui.Button(label="Next ▶", style=discord.ButtonStyle.secondary, row=1, disabled=(self.page >= total_pages - 1))
        next_btn.callback = self.next_page
        self.add_item(next_btn)

        start = self.page * items_per_page
        end = start + items_per_page
        current_page_items = fav_list[start:end]

        if current_page_items:
            play_options = []
            del_options = []
            for idx, item in enumerate(current_page_items, start):
                clean_title = sanitize_markdown(item.get("title", "Unknown Track"), max_len=55)
                added_date = str(item.get("added_at", ""))[:90]
                label_text = f"{idx + 1}. {clean_title}"[:100]
                play_options.append(discord.SelectOption(label=label_text, value=str(idx), description=added_date))
                del_options.append(discord.SelectOption(label=f"Delete #{idx + 1}: {clean_title[:80]}"[:100], value=str(idx), description=added_date))

            select = discord.ui.Select(placeholder="Select a song to queue/play...", options=play_options, row=2)
            select.callback = self.select_song
            self.add_item(select)

            remove_select = discord.ui.Select(placeholder="Delete a favorite...", options=del_options, row=3)
            remove_select.callback = self.remove_song
            self.add_item(remove_select)

    def get_embed(self):
        fav_list = self.get_list()
        title = "🌐 Server Favorites" if self.mode == "guild" else "👤 My Personal Favorites (All Servers)"
        embed = discord.Embed(title=title, color=discord.Color.gold())

        if not fav_list:
            embed.description = "No favorites saved yet! Use `;favorite` to save your first track."
            return embed

        items_per_page = 6
        total_pages = max(1, (len(fav_list) + items_per_page - 1) // items_per_page)
        self.page = min(self.page, total_pages - 1)

        start = self.page * items_per_page
        end = start + items_per_page
        current_slice = fav_list[start:end]

        lines = ""
        for idx, item in enumerate(current_slice, start + 1):
            clean_title = sanitize_markdown(item.get("title", "Unknown Track"), max_len=50)
            url = item.get("url", "")
            extra = f" • <@{item['user_id']}>" if self.mode == "guild" and "user_id" in item else ""
            line = f"`{idx}.` [{clean_title}]({url}){extra}\n"
            if len(lines) + len(line) < 3500:
                lines += line

        embed.description = lines
        embed.set_footer(text=f"Page {self.page + 1} of {total_pages} • Total saved: {len(fav_list)}")
        return embed

    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the command author can control this menu!", ephemeral=True)
            return
        if self.page > 0:
            self.page -= 1
            self.rebuild_ui()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the command author can control this menu!", ephemeral=True)
            return
        fav_list = self.get_list()
        total_pages = max(1, (len(fav_list) + 5) // 6)
        if self.page < total_pages - 1:
            self.page += 1
            self.rebuild_ui()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def toggle_mode(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Only the command author can control this menu!", ephemeral=True)
            return

        self.mode = "user" if self.mode == "guild" else "guild"
        self.page = 0
        self.rebuild_ui()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def play_all_favs(self, interaction: discord.Interaction):
        fav_list = self.get_list()
        if not fav_list:
            await interaction.response.send_message("No favorites to play!", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel first!", ephemeral=True)
            return

        await interaction.response.defer()

        voice_channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if not vc:
            vc = await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        state = get_music_state(interaction.guild.id)
        state["text_channel"] = self.ctx.channel

        for item in fav_list:
            state["queue"].append({
                "title": item["title"],
                "webpage_url": item["url"]
            })

        if not vc.is_playing() and not vc.is_paused():
            await play_next_track(interaction.guild.id)
            await self.ctx.send(f"Now playing all **{len(fav_list)}** favorite(s)! 🎶 {EMOJI_DANCING}")
        else:
            await self.ctx.send(f"Added all **{len(fav_list)}** favorite(s) to the queue! 🎶 {EMOJI_BLUSH}")

    async def select_song(self, interaction: discord.Interaction):
        fav_list = self.get_list()
        idx = int(interaction.data["values"][0])
        selected_track = fav_list[idx]

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel to play favorites!", ephemeral=True)
            return

        await interaction.response.defer()

        voice_channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if not vc:
            vc = await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        state = get_music_state(interaction.guild.id)
        state["text_channel"] = self.ctx.channel
        state["queue"].append({
            "title": selected_track["title"],
            "webpage_url": selected_track["url"]
        })

        if not vc.is_playing() and not vc.is_paused():
            await play_next_track(interaction.guild.id)
            await self.ctx.send(f"Now playing from favorites: **{selected_track['title']}**! {EMOJI_DANCING}")
        else:
            await self.ctx.send(f"Queued from favorites: **{selected_track['title']}** (Position #{len(state['queue'])}) {EMOJI_BLUSH}")

    async def remove_song(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("You cannot delete someone else's favorites!", ephemeral=True)
            return

        idx = int(interaction.data["values"][0])
        fav_list = self.get_list()

        if 0 <= idx < len(fav_list):
            removed = fav_list.pop(idx)
            save_favorites()
            self.rebuild_ui()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
            await self.ctx.send(f"Removed **{removed['title']}** from favorites.", delete_after=5)


# ============================================================
# PLAYLIST INTERACTIVE VIEW
# ============================================================

class PlaylistView(discord.ui.View):
    def __init__(self, ctx, pl_name: str, is_server: bool = False):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.pl_name = pl_name
        self.is_server = is_server
        self.page = 0
        self.update_buttons()

    def get_tracks(self):
        if self.is_server:
            return playlists_data["guilds"].get(str(self.ctx.guild.id), {}).get(self.pl_name, [])
        else:
            return playlists_data["users"].get(str(self.ctx.author.id), {}).get(self.pl_name, [])

    def get_embed(self):
        tracks = self.get_tracks()
        tag = "🌐 Server Playlist" if self.is_server else "👤 Personal Playlist"
        embed = discord.Embed(title=f"📋 {self.pl_name} ({tag})", color=discord.Color.blue())

        if not tracks:
            embed.description = "This playlist is currently empty!"
            return embed

        items_per_page = 8
        total_pages = max(1, (len(tracks) + items_per_page - 1) // items_per_page)
        self.page = min(self.page, total_pages - 1)

        start = self.page * items_per_page
        end = start + items_per_page
        current_slice = tracks[start:end]

        lines = ""
        for idx, t in enumerate(current_slice, start + 1):
            clean_title = sanitize_markdown(t["title"], max_len=50)
            lines += f"`{idx}.` [{clean_title}]({t['url']})\n"

        embed.description = lines
        embed.set_footer(text=f"Page {self.page + 1} of {total_pages} • Total tracks: {len(tracks)}")
        return embed

    def update_buttons(self):
        tracks = self.get_tracks()
        items_per_page = 8
        total_pages = max(1, (len(tracks) + items_per_page - 1) // items_per_page)

        self.prev_btn.disabled = (self.page <= 0)
        self.next_btn.disabled = (self.page >= total_pages - 1)

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        tracks = self.get_tracks()
        total_pages = max(1, (len(tracks) + 7) // 8)
        if self.page < total_pages - 1:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="▶️ Play Playlist", style=discord.ButtonStyle.success)
    async def play_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        tracks = self.get_tracks()
        if not tracks:
            await interaction.response.send_message("This playlist is empty!", ephemeral=True)
            return

        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message("You must be in a voice channel first!", ephemeral=True)
            return

        await interaction.response.defer()

        voice_channel = interaction.user.voice.channel
        vc = interaction.guild.voice_client
        if not vc:
            vc = await voice_channel.connect()
        elif vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        state = get_music_state(interaction.guild.id)
        state["text_channel"] = self.ctx.channel

        for item in tracks:
            state["queue"].append({
                "title": item["title"],
                "webpage_url": item["url"]
            })

        if not vc.is_playing() and not vc.is_paused():
            await play_next_track(interaction.guild.id)
            await self.ctx.send(f"Now playing playlist **{self.pl_name}** ({len(tracks)} tracks)! 🎶 {EMOJI_DANCING}")
        else:
            await self.ctx.send(f"Queued playlist **{self.pl_name}** ({len(tracks)} tracks)! 🎶 {EMOJI_BLUSH}")


# ============================================================
# COMMANDS
# ============================================================

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("I cannot kick a member whose highest role is equal to or higher than mine.")
        return
    await member.kick(reason=reason)
    await ctx.send(f"**{member}** was kicked.\nReason: {reason}")
    await log_action(
        ctx.guild, "Member Kicked", actor=ctx.author, target=member,
        details={"Reason": reason}, color=discord.Color.red()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("I cannot ban a member whose highest role is equal to or higher than mine.")
        return
    await member.ban(reason=reason)
    await ctx.send(f"**{member}** was banned.\nReason: {reason}")
    await log_action(
        ctx.guild, "Member Banned", actor=ctx.author, target=member,
        details={"Reason": reason}, color=discord.Color.red()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    user = await bot.fetch_user(user_id)
    try:
        await ctx.guild.unban(user)
    except discord.NotFound:
        await ctx.send("That user is not banned.")
        return
    await ctx.send(f"**{user}** was unbanned.")
    await log_action(
        ctx.guild, "Member Unbanned", actor=ctx.author, target=user,
        color=discord.Color.green()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    if minutes <= 0:
        await ctx.send("The timeout duration must be greater than 0.")
        return
    if member.top_role >= ctx.guild.me.top_role:
        await ctx.send("I cannot timeout a member whose role is equal to or higher than mine.")
        return
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    await ctx.send(f"**{member}** was timed out for `{minutes}` minute(s).\nReason: {reason}")
    await log_action(
        ctx.guild,
        "Member Timed Out",
        actor=ctx.author,
        target=member,
        details={"Duration": f"{minutes} minute(s)", "Reason": reason},
        color=discord.Color.orange()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(moderate_members=True)
async def untimeout(ctx, member: discord.Member):
    await member.timeout(None, reason=f"Timeout removed by {ctx.author}")
    await ctx.send(f"Timeout removed from **{member}**.")
    await log_action(
        ctx.guild, "Member Timeout Removed", actor=ctx.author, target=member,
        color=discord.Color.green()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    warnings = data.setdefault("warnings", {}).setdefault(str(ctx.guild.id), {}).setdefault(str(member.id), [])
    warnings.append({"reason": reason, "moderator": ctx.author.id})
    save_data()
    await ctx.send(f"⚠️ **{member}** has been warned.\nReason: {reason}\nTotal warnings: `{len(warnings)}`")
    await log_action(
        ctx.guild,
        "Member Warned",
        actor=ctx.author,
        target=member,
        details={"Reason": reason, "Total warnings": len(warnings)},
        color=discord.Color.orange()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
async def warnings(ctx, member: discord.Member):
    entries = data.get("warnings", {}).get(str(ctx.guild.id), {}).get(str(member.id), [])
    if not entries:
        await ctx.send(f"**{member}** has no warnings.")
        return
    embed = discord.Embed(title=f"Warnings — {member}", color=discord.Color.orange())
    for index, entry in enumerate(entries, 1):
        moderator = ctx.guild.get_member(entry["moderator"])
        moderator_name = str(moderator) if moderator else str(entry["moderator"])
        embed.add_field(
            name=f"Warning #{index}",
            value=f"Reason: {entry['reason']}\nModerator: {moderator_name}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
@commands.guild_only()
@moderator_only()
async def clearwarnings(ctx, member: discord.Member):
    data.get("warnings", {}).get(str(ctx.guild.id), {}).pop(str(member.id), None)
    save_data()
    await ctx.send(f"Cleared all warnings for **{member}**.")
    await log_action(
        ctx.guild, "Member Warnings Cleared", actor=ctx.author, target=member,
        color=discord.Color.orange()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(manage_messages=True, read_message_history=True)
async def purge(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Amount must be greater than 0.")
        return

    expected_deleted_ids = []
    try:
        expected_deleted_ids = [
            message.id
            async for message in ctx.channel.history(limit=amount + 1)
        ]
        purge_log_suppression.update(expected_deleted_ids)
        deleted = await ctx.channel.purge(
            limit=amount + 1,
            reason=f"Message purge requested by {ctx.author} ({ctx.author.id})"
        )
    except discord.Forbidden:
        purge_log_suppression.difference_update(expected_deleted_ids)
        await ctx.send("I need Manage Messages and Read Message History permissions to purge this channel.")
        return
    except discord.HTTPException as error:
        purge_log_suppression.difference_update(expected_deleted_ids)
        await ctx.send(f"Discord could not complete the purge: `{error}`")
        return

    deleted_ids = {message.id for message in deleted}
    purge_log_suppression.difference_update(set(expected_deleted_ids) - deleted_ids)
    purge_log_suppression.update(deleted_ids)

    deleted_count = sum(message.id != ctx.message.id for message in deleted)
    confirmation = await ctx.send(f"Deleted `{deleted_count}` message(s).")
    await confirmation.delete(delay=5)
    transcript = "\n".join(format_deleted_message(message) for message in deleted)
    transcript_chunks = [
        transcript[index:index + 950]
        for index in range(0, len(transcript), 950)
    ] or ["No message content was available."]
    for index, chunk in enumerate(transcript_chunks, start=1):
        await log_action(
            ctx.guild,
            "Messages Purged" if index == 1 else f"Messages Purged (continued {index})",
            actor=ctx.author,
            details={
                "Channel": ctx.channel.mention,
                "Deleted messages": deleted_count,
                "Message content": chunk,
            },
            color=discord.Color.orange()
        )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int):
    if not 0 <= seconds <= 21600:
        await ctx.send("Slowmode must be between 0 and 21600 seconds.")
        return
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"Slowmode set to `{seconds}` second(s).")
    await log_action(
        ctx.guild, "Channel Slowmode Changed", actor=ctx.author,
        details={"Channel": ctx.channel.mention, "Slowmode": f"{seconds} second(s)"},
        color=discord.Color.orange()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(manage_channels=True)
async def lock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Channel locked.")
    await log_action(
        ctx.guild, "Channel Locked", actor=ctx.author,
        details={"Channel": ctx.channel.mention}, color=discord.Color.orange()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(manage_channels=True)
async def unlock(ctx):
    overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None
    await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔓 Channel unlocked.")
    await log_action(
        ctx.guild, "Channel Unlocked", actor=ctx.author,
        details={"Channel": ctx.channel.mention}, color=discord.Color.green()
    )

@bot.command()
@commands.guild_only()
@moderator_only()
@commands.bot_has_permissions(manage_nicknames=True)
async def nick(ctx, member: discord.Member, *, nickname=None):
    await member.edit(nick=nickname, reason=f"Nickname changed by {ctx.author}")
    await log_action(
        ctx.guild, "Member Nickname Changed", actor=ctx.author, target=member,
        details={"New nickname": nickname or "Reset to account name"},
        color=discord.Color.orange()
    )
    if nickname:
        await ctx.send(f"Nickname changed for **{member}** to `{nickname}`.")
    else:
        await ctx.send(f"Nickname reset for **{member}**.")

@bot.command()
@commands.guild_only()
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=guild.name, color=discord.Color.blurple())
    embed.add_field(name="Owner", value=f"<@{guild.owner_id}>")
    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Channels", value=len(guild.channels))
    embed.add_field(name="Roles", value=len(guild.roles))
    embed.add_field(name="Server ID", value=guild.id)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command()
@commands.guild_only()
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=str(member), color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=str(member))
    embed.add_field(name="ID", value=member.id)
    embed.add_field(
        name="Joined Server",
        value=discord.utils.format_dt(member.joined_at, "F") if member.joined_at else "Unknown"
    )
    embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "F"))
    embed.add_field(name="Top Role", value=member.top_role.mention)
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"{member}'s Avatar", color=member.color)
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed)

@bot.command()
@commands.guild_only()
async def banner(ctx, member: discord.Member = None):
    member = member or ctx.author
    try:
        user = await bot.fetch_user(member.id)
    except discord.HTTPException:
        await ctx.send("Unable to fetch user profile.")
        return
    if not user.banner:
        await ctx.send(f"**{user}** does not have a dynamic banner configured.")
        return
    embed = discord.Embed(title=f"{user}'s Banner", color=member.color)
    embed.set_image(url=user.banner.url)
    await ctx.send(embed=embed)

@bot.command()
async def furry(ctx, member: discord.Member = None):
    member = member or ctx.author
    percentage = random.Random(member.id).randint(0, 100)
    if percentage < 30:
        message = f"{member.mention} is only **{percentage}%** furry! {EMOJI_SHOCKED}"
    elif percentage < 75:
        message = f"{member.mention} is **{percentage}%** furry! {EMOJI_SMIRK}"
    else:
        message = f"Oh my! {member.mention} is **{percentage}%** furry! {EMOJI_LOVE} {EMOJI_BLUSH}"
    await ctx.send(message)

@bot.command(aliases=["match"])
async def ship(ctx, user1: discord.Member, user2: discord.Member = None):
    if user2 is None:
        user1, user2 = ctx.author, user1
    if user1 == user2:
        await ctx.send(f"You can't ship someone with themselves! {EMOJI_BOYKISSER_HUH}")
        return
    ids = "".join(sorted((str(user1.id), str(user2.id))))
    percentage = random.Random(ids).randint(0, 100)
    if percentage < 25:
        message = f"💔 **{percentage}%**... {user1.mention} and {user2.mention} might want to stay friends. {EMOJI_SHOCKED}"
    elif percentage < 75:
        message = f"💛 **{percentage}%**! {user1.mention} and {user2.mention} have decent chemistry! {EMOJI_SMIRK}"
    else:
        message = f"💖 **{percentage}%**!!! {user1.mention} and {user2.mention} are a perfect match! {EMOJI_LOVE} {EMOJI_BLUSH}"
    await ctx.send(message)

@bot.command()
async def femboy(ctx, member: discord.Member = None):
    member = member or ctx.author
    percentage = random.Random(member.id).randint(0, 100)
    if percentage < 30:
        message = f"{member.mention} is only **{percentage}%** femboy! {EMOJI_SHOCKED}"
    elif percentage < 75:
        message = f"{member.mention} is **{percentage}%** femboy! {EMOJI_SMIRK}"
    else:
        message = f"Oh my! {member.mention} is **{percentage}%** femboy! {EMOJI_LOVE} {EMOJI_BLUSH}"
    await ctx.send(message)

@bot.command()
async def kiss(ctx, member: discord.Member = None):
    if not member:
        message = f"Please mention someone to kiss! {EMOJI_BOYKISSER_HUH}"
    elif member == ctx.author:
        message = f"You can't kiss yourself! But here is some love: {EMOJI_SHY}"
    else:
        message = f"{ctx.author.mention} kisses {member.mention}! {EMOJI_KISS_NEW} {EMOJI_LOVE}"
    await ctx.send(message)

@bot.command()
async def hug(ctx, member: discord.Member = None):
    if not member:
        message = f"Please mention someone to hug! {EMOJI_BOYKISSER_HUH}"
    elif member == ctx.author:
        message = f"Self hugs are okay, but here is a big embrace from me! {EMOJI_SHY} {EMOJI_LOVE}"
    else:
        message = f"{ctx.author.mention} gives {member.mention} a warm hug! {EMOJI_LOVE} {EMOJI_BLUSH}"
    await ctx.send(message)

@bot.command()
async def punch(ctx, member: discord.Member = None):
    if not member:
        message = f"Please mention someone to punch! {EMOJI_BOYKISSER_HUH}"
    elif member == ctx.author:
        message = f"Punching yourself? Don't do that! {EMOJI_BOYKISSER_HUH}"
    else:
        message = f"{ctx.author.mention} punches {member.mention}! {EMOJI_SHOCKED} {EMOJI_BOYKISSER_HUH}"
    await ctx.send(message)

@bot.command()
async def attack(ctx, member: discord.Member = None):
    if not member:
        await ctx.send(f"Please mention someone to attack! {EMOJI_BOYKISSER_HUH}")
        return
    if member == ctx.author:
        await ctx.send(f"Why are you trying to attack yourself? {EMOJI_BOYKISSER_HUH}")
        return
    await ctx.send(random.choice([
        f"{ctx.author.mention} charges at {member.mention} with a legendary tackle! {EMOJI_BOYKISSER_RIGHT}",
        f"{ctx.author.mention} attempts to attack {member.mention} with a pillow! {EMOJI_BOYKISSER_HAPPY}",
        f"{ctx.author.mention} throws a slice of hot pizza at {member.mention}! {EMOJI_PIZZA}"
    ]))

@bot.command()
async def boop(ctx, member: discord.Member = None):
    if not member:
        message = f"Please mention someone to boop! {EMOJI_BOYKISSER_HUH}"
    elif member == ctx.author:
        message = f"You boop your own nose. Cute! {EMOJI_BOYKISSER_BOOP}"
    else:
        message = f"{ctx.author.mention} gently boops {member.mention}'s nose! {EMOJI_BOYKISSER_BOOP}"
    await ctx.send(message)

@bot.command()
async def dance(ctx, member: discord.Member = None):
    if member:
        message = f"{ctx.author.mention} and {member.mention} start dancing! {EMOJI_DANCING}"
    else:
        message = f"{ctx.author.mention} breaks into an energetic dance! {EMOJI_DANCING}"
    await ctx.send(message)

async def render_captioned_gif(ctx, filename_base: str, meme_name: str, text: str):
    if not text or not text.strip():
        await ctx.send(f"Please provide some text for {meme_name}! {EMOJI_BOYKISSER_HUH}")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    names = [filename_base]
    if filename_base == "basketball.gif":
        names.extend(["basketball.png", "basketball.jpg", "basketball.jpeg",
                      "yaoming.gif", "yaoming.png", "yaoming.jpg", "yaoming.jpeg"])
    asset_path = next(
        (
            path
            for name in names
            for path in (os.path.join(script_dir, "assets", name), os.path.join(script_dir, name))
            if os.path.isfile(path)
        ),
        None
    )
    if asset_path is None:
        await ctx.send(f"**Error:** `{filename_base}` was not found in the assets or bot folder.")
        return

    status = await ctx.send(f"Generating {meme_name} GIF... please wait! {EMOJI_BOYKISSER_SEE}")
    output_path = os.path.join(
        script_dir,
        f"{os.path.splitext(os.path.basename(filename_base))[0]}_{ctx.message.id}.gif"
    )
    try:
        with Image.open(asset_path) as image:
            font = get_meme_font(28, script_dir)
            lines = _wrap_meme_text(text.strip(), image.width - 24, font, script_dir)
            line_height = 35
            caption_height = len(lines) * line_height + 24
            frames = []

            for frame in ImageSequence.Iterator(image):
                canvas = Image.new("RGBA", (image.width, image.height + caption_height), "white")
                canvas.paste(frame.convert("RGBA"), (0, caption_height))
                draw = ImageDraw.Draw(canvas)
                y = (caption_height - len(lines) * line_height) // 2
                for line in lines:
                    line_width = _meme_text_width(line, font, script_dir)
                    _draw_meme_text(
                        draw,
                        ((image.width - line_width) // 2, y),
                        line,
                        "black",
                        font,
                        script_dir
                    )
                    y += line_height
                frames.append(canvas.convert("RGB"))

            if not frames:
                raise ValueError(f"{filename_base} contains no frames")
            frames[0].save(
                output_path,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=image.info.get("duration") or 50,
                loop=image.info.get("loop", 0)
            )

        await ctx.send(file=discord.File(output_path))
        await status.delete()
    except (OSError, ValueError, discord.HTTPException) as error:
        await status.edit(content=f"Could not generate {meme_name}: `{error}`")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

@bot.command()
async def jarvis(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "jarvis.gif", "Jarvis", text)

@bot.command()
async def lowtiergod(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "lowtiergod.gif", "Low Tier God", text)

@bot.command(aliases=["floating", "ascend", "sponge"])
async def spongebob(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "spongebob.gif", "Spongebob Floating", text)

@bot.command(aliases=["tuff", "hoodiebob", "sadbob"])
async def tuffbob(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "tuffbob.gif", "Tuff Spongebob", text)

@bot.command(aliases=["fanum", "food"])
async def fanumfood(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "fanumfood.gif", "Fanum Food", text)

@bot.command(aliases=["pilot", "crossview"])
async def stephen(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "stephen.jpg", "Stephen", text)

@bot.command(aliases=["reason", "heartbeats"])
async def katanaman(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "reason.gif", "Katana Man", text)

@bot.command(aliases=["yaoming", "cried"])
async def basketball(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "basketball.gif", "Basketball", text)

@bot.command()
async def tryhard(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "tryhard.gif", "Tryhard", text)

@bot.command()
async def bkleash(ctx, *, text: str = None):
    await render_captioned_gif(ctx, "boykisser-leash.gif", "Boykisser Leash", text)

@bot.command()
async def lockin(ctx, *, text: str = None):
    if not text or "|" not in text:
        await ctx.send(
            f"Provide two captions separated by `|`.\n"
            f"**Usage:** `{get_prefix(bot, ctx.message)}lockin <first caption> | <second caption>`"
        )
        return

    first_caption, _, second_caption = text.partition("|")
    captions = [first_caption.strip(), second_caption.strip()]
    if not all(captions):
        await ctx.send("Both captions are required, one on each side of `|`.")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, "assets", "lockin.png")
    if not os.path.isfile(template_path):
        template_path = os.path.join(script_dir, "lockin.png")
    if not os.path.isfile(template_path):
        await ctx.send("**Error:** `lockin.png` was not found in the assets or bot folder.")
        return

    status = await ctx.send(f"Generating Lock In meme... please wait! {EMOJI_BOYKISSER_SEE}")
    output_path = os.path.join(script_dir, f"lockin_{ctx.message.id}.gif")
    try:
        with Image.open(template_path) as source:
            image = source.convert("RGB")
        draw = ImageDraw.Draw(image)
        divider_x = image.width // 2
        panel_bottom = int(image.height * 0.285)
        panels = [
            (24, 12, divider_x - 18, panel_bottom - 12),
            (divider_x + 18, 12, image.width - 24, panel_bottom - 12),
        ]

        for caption, (left, top, right, bottom) in zip(captions, panels):
            max_width = right - left
            max_height = bottom - top
            for font_size in range(52, 13, -2):
                font = get_meme_font(font_size, script_dir)
                wrapped = _wrap_meme_text(caption, max_width, font, script_dir)
                line_height = int(font_size * 1.2)
                widths = [_meme_text_width(line, font, script_dir) for line in wrapped]
                if max(widths, default=0) <= max_width and len(wrapped) * line_height <= max_height:
                    break

            y = top + (max_height - len(wrapped) * line_height) // 2
            for line, line_width in zip(wrapped, widths):
                _draw_meme_text(
                    draw,
                    (left + (max_width - line_width) // 2, y),
                    line,
                    "black",
                    font,
                    script_dir
                )
                y += line_height

        image.save(output_path, format="GIF")
        await ctx.send(file=discord.File(output_path))
        await status.delete()
    except (OSError, ValueError, discord.HTTPException) as error:
        await status.edit(content=f"Could not generate Lock In meme: `{error}`")
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)

@bot.command()
@moderator_only()
async def announce(ctx, *, message):
    embed = discord.Embed(title="Announcement", description=message, color=discord.Color.blurple())
    embed.set_footer(text=f"Posted by {ctx.author}")
    await ctx.send("@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
    await log_action(
        ctx.guild, "Announcement Posted", actor=ctx.author,
        details={"Channel": ctx.channel.mention, "Announcement": message},
        color=discord.Color.blurple()
    )

@bot.command()
@owner_only()
@commands.guild_only()
async def setlog(ctx, channel: discord.TextChannel):
    data["logs"][str(ctx.guild.id)] = channel.id
    save_data()
    await ctx.send(f"Moderation logs will now be sent to {channel.mention}.")

@bot.command()
@owner_only()
@commands.guild_only()
async def disablelog(ctx):
    data["logs"].pop(str(ctx.guild.id), None)
    save_data()
    await ctx.send("Moderation logging disabled.")


# ============================================================
# PAGINATED HELP SYSTEM (UI BUTTONS)
# ============================================================

class HelpPaginator(discord.ui.View):
    def __init__(self, author, pages):
        super().__init__(timeout=120)
        self.author = author
        self.pages = pages
        self.current_page = 0
        self.message = None
        self.update_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                f"You cannot control someone else's help menu! {EMOJI_BOYKISSER_HUH}",
                ephemeral=True
            )
            return False
        return True

    def update_buttons(self):
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.pages) - 1)

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

@bot.command(name="help")
async def help_command(ctx):
    prefix = get_prefix(bot, ctx.message)
    pages = []

    embed1 = discord.Embed(
        title="🛡️ Moderation Commands",
        description="ID-Restricted moderation tools for authorized staff.",
        color=discord.Color.red()
    )
    embed1.add_field(
        name="Commands",
        value=(
            f"`{prefix}kick @user [reason]`\n"
            f"`{prefix}ban @user [reason]`\n"
            f"`{prefix}unban <user ID>`\n"
            f"`{prefix}timeout @user <minutes> [reason]`\n"
            f"`{prefix}untimeout @user`\n"
            f"`{prefix}warn @user [reason]`\n"
            f"`{prefix}warnings @user`\n"
            f"`{prefix}clearwarnings @user`\n"
            f"`{prefix}purge <amount>`\n"
            f"`{prefix}slowmode <seconds>`\n"
            f"`{prefix}lock`\n"
            f"`{prefix}unlock`"
        ),
        inline=False
    )
    pages.append(embed1)

    embed2 = discord.Embed(
        title="⚙️ Server & Utility Commands",
        description="General server discovery and user profiling commands.",
        color=discord.Color.blurple()
    )
    embed2.add_field(
        name="Commands",
        value=(
            f"`{prefix}serverinfo` — Displays server stats\n"
            f"`{prefix}userinfo [@user]` — Displays account details\n"
            f"`{prefix}avatar [@user]` — Displays user profile picture\n"
            f"`{prefix}banner [@user]` — Displays user profile banner\n"
            f"`{prefix}nick @user <nickname>` — Update nicknames\n"
            f"`{prefix}announce <msg>` — Send an @everyone announcement\n"
            f"`{prefix}ping` — View bot ping latency\n"
            f"`{prefix}botinfo` — System statistics and bot version\n"
            f"`{prefix}prefix <new prefix>` — Custom command prefix"
        ),
        inline=False
    )
    pages.append(embed2)

    embed3 = discord.Embed(
        title="🐾 Fun & Action Commands",
        description="Interact and play with server members.",
        color=discord.Color.green()
    )
    embed3.add_field(
        name="Commands",
        value=(
            f"`{prefix}furry [@user]` — Check how furry someone is\n"
            f"`{prefix}femboy [@user]` — Check how femboy someone is\n"
            f"`{prefix}ship @user1 [@user2]` — Calculate the ship chemistry between two users\n"
            f"`{prefix}kiss @user` — Kiss another member\n"
            f"`{prefix}hug @user` — Give another member a hug\n"
            f"`{prefix}punch @user` — Punch someone\n"
            f"`{prefix}attack @user` — Perform an attack on someone\n"
            f"`{prefix}boop @user` — Gently boop a member's nose\n"
            f"`{prefix}dance [@user]` — Dance alone or with a partner"
        ),
        inline=False
    )
    pages.append(embed3)

    embed4 = discord.Embed(
        title="🎬 Memes & Quotes",
        description="Generate animated caption GIFs, panel GIFs, and quotes. *(All output as .gif with Impact font)*",
        color=discord.Color.gold()
    )
    embed4.add_field(
        name="Commands",
        value=(
            f"`{prefix}jarvis <text>` — Caption the Jarvis explanation GIF\n"
            f"`{prefix}lowtiergod <text>` — Caption the Low Tier God GIF\n"
            f"`{prefix}spongebob <text>` — Caption Spongebob floating to music\n"
            f"`{prefix}tuffbob <text>` — Caption the Tuff Spongebob GIF\n"
            f"`{prefix}fanumfood <text>` — Caption the Fanum Food GIF\n"
            f"`{prefix}stephen <text>` — Caption the Stephen meme\n"
            f"`{prefix}katanaman <text>` — Fill the Katana Man manga panel\n"
            f"`{prefix}basketball <text>` — Yao Ming meme with any custom text\n"
            f"`{prefix}tryhard <text>` — Caption the Tryhard meme GIF\n"
            f"`{prefix}bkleash <text>` — Caption the Boykisser Leash meme GIF\n"
            f"`{prefix}lockin <first caption> | <second caption>` — Caption both panels of the Lock In meme\n"
            f"`{prefix}quotethis` — Reply to a message with this command to quote it!"
        ),
        inline=False
    )
    pages.append(embed4)

    embed5 = discord.Embed(
        title="🎵 Music & Audio Suite",
        description="Interactive music playback, queue management, playlists, and favorites.",
        color=discord.Color.purple()
    )
    embed5.add_field(
        name="Playback & Queue",
        value=(
            f"`{prefix}play <query/URL>` — Play a track or full URL playlist\n"
            f"`{prefix}playfile` — Play one audio file attached to the command or its replied-to message\n"
            f"`{prefix}queue` — Interactive queue with pagination & controls\n"
            f"`{prefix}nowplaying` — Live track player with interactive buttons\n"
            f"`{prefix}effect` — Interactive dropdown to select audio filters\n"
            f"`{prefix}autorestartfx` — Toggle auto-restart on effect apply\n"
            f"`{prefix}restartsong` — Restart the currently playing track\n"
            f"`{prefix}volume [1-100]` — View or set audio output volume\n"
            f"`{prefix}loop` — Toggle looping current song\n"
            f"`{prefix}skip` / `{prefix}stop` — Control audio stream\n"
            f"`{prefix}join` / `{prefix}leave` — Summon or disconnect bot"
        ),
        inline=False
    )
    embed5.add_field(
        name="Favorites & Custom Playlists",
        value=(
            f"`{prefix}favorite` — Save current song or link to favorites\n"
            f"`{prefix}favorites` — Interactive favorites manager (with Play All!)\n"
            f"`{prefix}playlist create <name> [--server]` — Create personal or server playlist\n"
            f"`{prefix}playlist add <name> [url] [--server]` — Add track to playlist\n"
            f"`{prefix}playlist play <name> [--server]` — Queue and play a playlist\n"
            f"`{prefix}playlist list [--server]` — View all saved playlists\n"
            f"`{prefix}playlist view <name> [--server]` — View tracks in a playlist\n"
            f"`{prefix}playlist remove <name> <num> [--server]` — Delete track from playlist\n"
            f"`{prefix}playlist delete <name> [--server]` — Delete an entire playlist"
        ),
        inline=False
    )
    pages.append(embed5)

    embed6 = discord.Embed(
        title="🛠️ Config & Developer Tools",
        description="Logging options, auto-replies, and isolated dev testing.",
        color=discord.Color.dark_gray()
    )
    embed6.add_field(
        name="Commands",
        value=(
            f"`{prefix}chat <msg>` — Chat with the local AI\n"
            f"`{prefix}persona <name>` — Change AI personality\n"
            f"`{prefix}restart` — Reboot the bot (Owner only)\n"
            f"`{prefix}disable <cmd> [--global]` — Disable command (Owner only)\n"
            f"`{prefix}enable <cmd> [--global]` — Enable command (Owner only)\n"
            f"`{prefix}blacklist` — Manage user blacklists (Owner only)\n"
            f"`{prefix}setlog #channel` — Set logging destination\n"
            f"`{prefix}disablelog` — Disable logging\n"
            f"`{prefix}devtest` — Lock Penny into a temporary test channel\n"
            f"`{prefix}undevtest` — Delete test room and unlock bot activity"
        ),
        inline=False
    )
    pages.append(embed6)

    total_pages = len(pages)
    for idx, page in enumerate(pages, 1):
        page.set_footer(text=f"Page {idx} of {total_pages} • Prefix: {prefix}")

    view = HelpPaginator(ctx.author, pages)
    view.message = await ctx.send(embed=pages[0], view=view)


# ============================================================
# BOT DISABLING / ENABLING CONFIGURATION
# ============================================================

@bot.command()
@owner_only()
async def disable(ctx, cmd_name: str, *, flag: str = ""):
    cmd = bot.get_command(cmd_name)
    if not cmd:
        await ctx.send(f"Command `{cmd_name}` not found! {EMOJI_BOYKISSER_HUH}")
        return
    
    real_name = cmd.name
    if real_name in ["enable", "disable", "restart", "help"]:
        await ctx.send(f"You cannot disable the `{real_name}` command! That's a bad idea. {EMOJI_SHOCKED}")
        return

    is_global = "--global" in flag.lower()
    disabled = data.setdefault("disabled_commands", {"global": [], "guilds": {}})

    if is_global:
        if real_name not in disabled["global"]:
            disabled["global"].append(real_name)
            save_data()
            await ctx.send(f"🚫 Command `{real_name}` has been disabled **globally**.")
        else:
            await ctx.send(f"Command `{real_name}` is already disabled globally.")
    else:
        guild_id = str(ctx.guild.id)
        g_disabled = disabled["guilds"].setdefault(guild_id, [])
        if real_name not in g_disabled:
            g_disabled.append(real_name)
            save_data()
            await ctx.send(f"🚫 Command `{real_name}` has been disabled **in this server**.")
        else:
            await ctx.send(f"Command `{real_name}` is already disabled in this server.")

@bot.command()
@owner_only()
async def enable(ctx, cmd_name: str, *, flag: str = ""):
    cmd = bot.get_command(cmd_name)
    if not cmd:
        await ctx.send(f"Command `{cmd_name}` not found! {EMOJI_BOYKISSER_HUH}")
        return
    
    real_name = cmd.name
    is_global = "--global" in flag.lower()
    disabled = data.setdefault("disabled_commands", {"global": [], "guilds": {}})

    if is_global:
        if real_name in disabled["global"]:
            disabled["global"].remove(real_name)
            save_data()
            await ctx.send(f"✅ Command `{real_name}` has been enabled **globally**.")
        else:
            await ctx.send(f"Command `{real_name}` is not globally disabled.")
    else:
        guild_id = str(ctx.guild.id)
        g_disabled = disabled["guilds"].get(guild_id, [])
        if real_name in g_disabled:
            g_disabled.remove(real_name)
            save_data()
            await ctx.send(f"✅ Command `{real_name}` has been enabled **in this server**.")
        else:
            await ctx.send(f"Command `{real_name}` is not disabled in this server.")


# ============================================================
# BOT BLACKLIST CONFIGURATION
# ============================================================

@bot.group(invoke_without_command=True)
@owner_only()
async def blacklist(ctx):
    prefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(
        title="🚫 Blacklist Configuration",
        description=(
            f"`{prefix}blacklist add @user [command]` — Block a user from using all or specific commands\n"
            f"`{prefix}blacklist remove @user [command]` — Unblock a user\n"
            f"`{prefix}blacklist list` — View all blacklisted users"
        ),
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

@blacklist.command(name="add")
@owner_only()
async def blacklist_add(ctx, user: discord.User, cmd_name: str = None):
    if user.id in OWNER_IDS:
        await ctx.send("You cannot blacklist an owner!")
        return

    bl = data.setdefault("blacklist", {"all": []})

    if not cmd_name:
        if user.id in bl["all"]:
            await ctx.send(f"**{user.name}** is already fully blacklisted.")
        else:
            bl["all"].append(user.id)
            save_data()
            await ctx.send(f"Added **{user.name}** to the total blacklist. They can no longer use any commands.")
    else:
        cmd = bot.get_command(cmd_name)
        if not cmd:
            await ctx.send(f"Command `{cmd_name}` not found! {EMOJI_BOYKISSER_HUH}")
            return
        real_name = cmd.name
        c_list = bl.setdefault(real_name, [])
        if user.id in c_list:
            await ctx.send(f"**{user.name}** is already blacklisted from `{real_name}`.")
        else:
            c_list.append(user.id)
            save_data()
            await ctx.send(f"Added **{user.name}** to the blacklist specifically for the `{real_name}` command.")

@blacklist.command(name="remove")
@owner_only()
async def blacklist_remove(ctx, user: discord.User, cmd_name: str = None):
    bl = data.setdefault("blacklist", {"all": []})

    if not cmd_name:
        if user.id in bl["all"]:
            bl["all"].remove(user.id)
            save_data()
            await ctx.send(f"Removed **{user.name}** from the total blacklist.")
        else:
            await ctx.send(f"**{user.name}** is not in the total blacklist.")
    else:
        cmd = bot.get_command(cmd_name)
        if not cmd:
            real_name = cmd_name
        else:
            real_name = cmd.name

        c_list = bl.get(real_name, [])
        if user.id in c_list:
            c_list.remove(user.id)
            if not c_list:
                del bl[real_name]
            save_data()
            await ctx.send(f"Removed **{user.name}** from the `{real_name}` blacklist.")
        else:
            await ctx.send(f"**{user.name}** is not blacklisted from `{real_name}`.")

@blacklist.command(name="list")
@owner_only()
async def blacklist_list(ctx):
    bl = data.get("blacklist", {"all": []})
    if not bl or (not bl.get("all") and all(not v for v in bl.values())):
        await ctx.send("The blacklist is currently empty.")
        return

    embed = discord.Embed(title="🚫 Blacklisted Users", color=discord.Color.red())

    if bl.get("all"):
        embed.add_field(name="Full Blacklist (All Commands)", value="\n".join(f"• <@{uid}> (`{uid}`)" for uid in bl["all"]), inline=False)

    for cmd_key, uids in bl.items():
        if cmd_key != "all" and uids:
            embed.add_field(name=f"Command: {cmd_key}", value="\n".join(f"• <@{uid}>" for uid in uids), inline=False)

    await ctx.send(embed=embed)


# ============================================================
# BOT RESTART COMMAND (CLEAN PROCESS REPLACEMENT)
# ============================================================

@bot.command()
@owner_only()
async def restart(ctx):
    embed = discord.Embed(
        title="🔄 Restarting Penny",
        description="Saving persistent data and cleanly rebooting process...",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

    for vc in list(bot.voice_clients):
        try:
            await update_vc_status(vc.channel, None)
            await vc.disconnect()
        except Exception:
            pass

    save_data()
    save_favorites()
    save_playlists()

    await bot.close()

    subprocess.Popen([sys.executable] + sys.argv)
    sys.exit(0)


# ============================================================
# MUSIC COMMANDS
# ============================================================

@bot.command(aliases=["p"])
async def play(ctx, *, query: str = None):
    if not query:
        await ctx.send(f"Please provide a song title or URL! {EMOJI_BOYKISSER_HUH}")
        return

    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(f"You must be in a voice channel first! {EMOJI_BOYKISSER_HUH}")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = ctx.guild.voice_client

    if not voice_client:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    state = get_music_state(ctx.guild.id)
    state["text_channel"] = ctx.channel

    status_msg = await ctx.send(f"Searching and loading... {EMOJI_BOYKISSER_SEE}")

    loop = asyncio.get_event_loop()
    try:
        def _extract():
            with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
                return ydl.extract_info(query, download=False)

        info = await loop.run_in_executor(None, _extract)
    except Exception as e:
        await status_msg.edit(content=f"Failed to fetch song: `{e}`")
        return

    if not info:
        await status_msg.edit(content=f"No results found for `{query}`.")
        return

    entries = []
    is_search = info.get('extractor_key') in ['YoutubeSearch', 'YoutubeSearchURL']

    if 'entries' in info and not is_search:
        for entry in info['entries']:
            if entry:
                clean_title = sanitize_markdown(entry.get('title', 'Unknown Track'), max_len=60)
                video_url = entry.get('webpage_url')
                if not video_url and entry.get('id'):
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                elif not video_url:
                    video_url = entry.get('url')

                entries.append({
                    'title': clean_title,
                    'webpage_url': video_url
                })
        for t in entries:
            state["queue"].append(t)
        await status_msg.edit(content=f"Queued **{len(entries)} tracks** from playlist `{info.get('title', 'Playlist')[:50]}`! {EMOJI_PIZZA}")
    else:
        target = info['entries'][0] if 'entries' in info and info['entries'] else info
        clean_title = sanitize_markdown(target.get('title', 'Unknown Track'), max_len=60)
        
        video_url = target.get('webpage_url')
        if not video_url and target.get('id'):
            video_url = f"https://www.youtube.com/watch?v={target['id']}"
        elif not video_url:
            video_url = target.get('url')

        track_item = {
            'title': clean_title,
            'webpage_url': video_url
        }
        state["queue"].append(track_item)
        if voice_client.is_playing() or voice_client.is_paused():
            await status_msg.edit(content=f"Added to queue: **{clean_title}** (Position #{len(state['queue'])}) {EMOJI_BLUSH}")
        else:
            await status_msg.delete()

    if not voice_client.is_playing() and not voice_client.is_paused():
        await play_next_track(ctx.guild.id)

@bot.command()
@commands.guild_only()
async def playfile(ctx):
    attachments = ctx.message.attachments
    if (
        not attachments
        and ctx.message.reference
        and ctx.message.reference.message_id
    ):
        referenced_message = ctx.message.reference.resolved
        if referenced_message is None:
            try:
                referenced_message = await ctx.channel.fetch_message(
                    ctx.message.reference.message_id
                )
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                await ctx.send("I couldn't retrieve the message you replied to.")
                return
        attachments = referenced_message.attachments

    if not attachments:
        await ctx.send(
            f"Attach one audio file to your `{get_prefix(bot, ctx.message)}playfile` "
            "message, or reply to a message containing an audio file."
        )
        return

    if len(attachments) != 1:
        await ctx.send("Please attach exactly one audio file.")
        return

    attachment = attachments[0]
    supported_extensions = {
        ".aac", ".flac", ".m4a", ".mp3", ".oga", ".ogg", ".opus",
        ".wav", ".webm", ".wma",
    }
    extension = os.path.splitext(attachment.filename)[1].lower()
    if extension not in supported_extensions:
        supported = ", ".join(sorted(supported_extensions))
        await ctx.send(f"Unsupported audio file type. Supported extensions: `{supported}`.")
        return

    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(f"You must be in a voice channel first! {EMOJI_BOYKISSER_HUH}")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = ctx.guild.voice_client
    if not voice_client:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)

    state = get_music_state(ctx.guild.id)
    state["text_channel"] = ctx.channel
    track = {
        "title": sanitize_markdown(os.path.splitext(attachment.filename)[0], max_len=60),
        "webpage_url": attachment.url,
        "is_attachment": True,
    }
    state["queue"].append(track)

    if voice_client.is_playing() or voice_client.is_paused():
        await ctx.send(f"Added uploaded audio to the queue: **{track['title']}**.")
    else:
        await ctx.send(f"Playing uploaded audio: **{track['title']}**.")
        await play_next_track(ctx.guild.id)

@bot.command(aliases=["s", "next"])
async def skip(ctx):
    vc = ctx.guild.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        await ctx.send(f"Nothing is currently playing to skip! {EMOJI_BOYKISSER_HUH}")
        return

    vc.stop()
    await ctx.send(f"Skipped track! {EMOJI_BOYKISSER_RIGHT}")

@bot.command(aliases=["replay"])
async def restartsong(ctx):
    state = get_music_state(ctx.guild.id)
    vc = ctx.guild.voice_client
    if not vc or not (vc.is_playing() or vc.is_paused()) or not state["current"]:
        await ctx.send(f"Nothing is currently playing to restart! {EMOJI_BOYKISSER_HUH}")
        return

    current_track = state["current"]
    state["queue"].insert(0, current_track)
    state["current"] = None
    vc.stop()
    await ctx.send(f"Restarted **{current_track['title']}**! 🔄")

@bot.command()
async def pause(ctx):
    vc = ctx.guild.voice_client
    if vc and vc.is_playing():
        vc.pause()
        await ctx.send(f"Paused playback. {EMOJI_BOYKISSER_SMOKING}")
    else:
        await ctx.send(f"Nothing is currently playing! {EMOJI_BOYKISSER_HUH}")

@bot.command()
async def resume(ctx):
    vc = ctx.guild.voice_client
    if vc and vc.is_paused():
        vc.resume()
        await ctx.send(f"Resumed playback! {EMOJI_DANCING}")
    else:
        await ctx.send(f"Playback is not paused! {EMOJI_BOYKISSER_HUH}")

@bot.command()
async def stop(ctx):
    state = get_music_state(ctx.guild.id)
    state["queue"].clear()
    state["current"] = None
    state["loop"] = False

    vc = ctx.guild.voice_client
    if vc:
        await update_vc_status(vc.channel, None)
        if vc.is_playing() or vc.is_paused():
            vc.stop()

    await ctx.send(f"Stopped music and cleared the queue. {EMOJI_SHOCKED}")
    await schedule_disconnect(ctx.guild.id, delay=180)

@bot.command(aliases=["q"])
async def queue(ctx):
    view = InteractiveQueueView(ctx.guild.id)
    embed = view.get_embed()
    await ctx.send(embed=embed, view=view)

@bot.command(aliases=["np"])
async def nowplaying(ctx):
    state = get_music_state(ctx.guild.id)
    if not state["current"]:
        await ctx.send(f"Nothing is currently playing. {EMOJI_BOYKISSER_HUH}")
        return

    track = state["current"]
    fx = f"`{state['effect']}`" if state['effect'] != "none" else "None"
    loop_txt = "Enabled" if state['loop'] else "Disabled"
    clean_title = sanitize_markdown(track["title"], max_len=60)

    embed = discord.Embed(
        title="🎵 Now Playing",
        description=f"[{clean_title}]({track['webpage_url']})",
        color=discord.Color.purple()
    )
    embed.add_field(name="Volume", value=f"{int(state['volume'] * 100)}%", inline=True)
    embed.add_field(name="Effect", value=fx, inline=True)
    embed.add_field(name="Loop", value=loop_txt, inline=True)

    view = NowPlayingView(ctx.guild.id)
    await ctx.send(embed=embed, view=view)

@bot.command(aliases=["vol"])
async def volume(ctx, vol: int = None):
    state = get_music_state(ctx.guild.id)
    if vol is None:
        await ctx.send(f"Current volume is `{int(state['volume'] * 100)}%`. {EMOJI_BLUSH}")
        return

    if vol < 1 or vol > 100:
        await ctx.send("Please provide a volume between 1 and 100.")
        return

    state["volume"] = vol / 100

    vc = ctx.guild.voice_client
    if vc and vc.source and hasattr(vc.source, "volume"):
        vc.source.volume = state["volume"]

    await ctx.send(f"Volume adjusted to `{vol}%`. {EMOJI_BLUSH}")

@bot.command()
async def loop(ctx):
    state = get_music_state(ctx.guild.id)
    state["loop"] = not state["loop"]
    status = "enabled" if state["loop"] else "disabled"
    await ctx.send(f"Track looping is now **{status}**. {EMOJI_DANCING}")

@bot.command(aliases=["effects", "filter"])
async def effect(ctx, effect_name: str = None):
    state = get_music_state(ctx.guild.id)
    if effect_name:
        effect_name = effect_name.lower()
        if effect_name not in EFFECT_FILTERS:
            available = ", ".join(f"`{k}`" for k in EFFECT_FILTERS.keys())
            await ctx.send(f"Unknown effect `{effect_name}`. Available: {available} {EMOJI_BOYKISSER_HUH}")
            return

        state["effect"] = effect_name
        restarted_note = ""

        vc = ctx.guild.voice_client
        if state["autorestart_on_effect"] and vc and (vc.is_playing() or vc.is_paused()) and state["current"]:
            current_track = state["current"]
            state["queue"].insert(0, current_track)
            state["current"] = None
            vc.stop()
            restarted_note = " *(Track automatically restarted with new effect)*"

        await ctx.send(f"Audio effect set to `{effect_name}`!{restarted_note} {EMOJI_BOYKISSER_HAPPY}")
        return

    embed = discord.Embed(
        title="🎛️ Audio Effects Menu",
        description="Select an effect below or toggle auto-restarting the current track when an effect is chosen.",
        color=discord.Color.purple()
    )
    view = EffectSelectView(ctx.guild.id)
    await ctx.send(embed=embed, view=view)

@bot.command(aliases=["autorestartfx", "autorestarteffect"])
async def autorestart(ctx):
    state = get_music_state(ctx.guild.id)
    state["autorestart_on_effect"] = not state["autorestart_on_effect"]
    status = "enabled" if state["autorestart_on_effect"] else "disabled"
    await ctx.send(f"Auto-restart on effect apply is now **{status}**. {EMOJI_BLUSH}")


# ============================================================
# FAVORITES SYSTEM
# ============================================================

@bot.command(aliases=["fav"])
async def favorite(ctx, *, query: str = None):
    state = get_music_state(ctx.guild.id)
    target_track = None

    if query:
        loop = asyncio.get_event_loop()
        try:
            def _extract():
                with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
                    return ydl.extract_info(query, download=False)
            data_info = await loop.run_in_executor(None, _extract)
            if 'entries' in data_info and data_info['entries']:
                entry = data_info['entries'][0]
                target_track = {'title': entry.get('title', 'Unknown Track'), 'webpage_url': entry.get('webpage_url') or entry.get('url')}
            else:
                target_track = {'title': data_info.get('title', 'Unknown Track'), 'webpage_url': data_info.get('webpage_url') or data_info.get('url')}
        except Exception as e:
            await ctx.send(f"Failed to lookup song: `{e}`")
            return
    elif state["current"]:
        target_track = state["current"]
    else:
        await ctx.send(f"No song is currently playing! Provide a link or search query: `;favorite <query>` {EMOJI_BOYKISSER_HUH}")
        return

    target_url = target_track.get("webpage_url") or ""
    target_host = urllib.parse.urlparse(target_url).hostname
    if target_track.get("is_attachment") or target_host in {
        "cdn.discordapp.com",
        "cdn.discordapp.net",
        "media.discordapp.net",
    }:
        await ctx.send("Uploaded Discord audio files cannot be added to favorites.")
        return

    guild_id_str = str(ctx.guild.id)
    user_id_str = str(ctx.author.id)

    clean_title = sanitize_markdown(target_track["title"], max_len=60)
    fav_item_guild = {
        "title": clean_title,
        "url": target_track["webpage_url"],
        "user_id": ctx.author.id,
        "user_name": str(ctx.author),
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    fav_item_user = {
        "title": clean_title,
        "url": target_track["webpage_url"],
        "guild_id": ctx.guild.id,
        "guild_name": ctx.guild.name,
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    g_list = favorites_data["guilds"].setdefault(guild_id_str, [])
    if not any(item["url"] == target_track["webpage_url"] for item in g_list):
        g_list.append(fav_item_guild)

    u_list = favorites_data["users"].setdefault(user_id_str, [])
    if not any(item["url"] == target_track["webpage_url"] for item in u_list):
        u_list.append(fav_item_user)

    save_favorites()
    await ctx.send(f"Saved **{clean_title}** to favorites! ❤️ {EMOJI_LOVE}")

@bot.command(aliases=["favs"])
async def favorites(ctx):
    view = FavoritesView(ctx, mode="guild")
    embed = view.get_embed()
    await ctx.send(embed=embed, view=view)


# ============================================================
# PLAYLISTS SYSTEM (PERSONAL & SERVER)
# ============================================================

@bot.group(invoke_without_command=True, aliases=["pl", "playlists"])
async def playlist(ctx):
    prefix = get_prefix(bot, ctx.message)
    embed = discord.Embed(
        title="📋 Playlist System",
        description=(
            f"Manage personal and server-wide custom playlists.\n"
            f"Add `--server` to manage a server playlist (Moderators only).\n\n"
            f"**Commands:**\n"
            f"`{prefix}playlist create <name> [--server]`\n"
            f"`{prefix}playlist add <name> [url/query] [--server]`\n"
            f"`{prefix}playlist play <name> [--server]`\n"
            f"`{prefix}playlist list [--server]`\n"
            f"`{prefix}playlist view <name> [--server]`\n"
            f"`{prefix}playlist remove <name> <song_number> [--server]`\n"
            f"`{prefix}playlist delete <name> [--server]`"
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def join(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(f"You must be in a voice channel first! {EMOJI_BOYKISSER_HUH}")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.guild.voice_client

    if voice_client:
        await voice_client.move_to(channel)
    else:
        await channel.connect()

    await ctx.send(f"Connected to **#{channel.name}**! {EMOJI_BOYKISSER_HAPPY}")

@bot.command(aliases=["disconnect"])
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client:
        state = get_music_state(ctx.guild.id)
        state["queue"].clear()
        state["current"] = None
        state["loop"] = False
        await update_vc_status(voice_client.channel, None)
        await voice_client.disconnect()
        music_states.pop(ctx.guild.id, None)
        await ctx.send(f"Disconnected from voice channel. {EMOJI_BOYKISSER_SMOKING}")
    else:
        await ctx.send(f"I am not connected to any voice channel in this server. {EMOJI_BOYKISSER_HUH}")


# ============================================================
# QUOTE COMMAND
# ============================================================

@bot.command(aliases=["quote"])
async def quotethis(ctx):
    if not ctx.message.reference or not ctx.message.reference.message_id:
        await ctx.send(f"You must reply to a message to quote it! {EMOJI_BOYKISSER_HUH}")
        return

    try:
        quoted_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
    except (discord.NotFound, discord.HTTPException):
        await ctx.send(f"Could not retrieve the quoted message. {EMOJI_SHOCKED}")
        return

    embed = discord.Embed(
        description=quoted_msg.content if quoted_msg.content else "*[No text content]*",
        color=quoted_msg.author.color,
        timestamp=quoted_msg.created_at
    )
    embed.set_author(
        name=f"{quoted_msg.author.display_name} (@{quoted_msg.author.name})",
        icon_url=quoted_msg.author.display_avatar.url,
        url=quoted_msg.jump_url
    )

    if quoted_msg.attachments:
        for attachment in quoted_msg.attachments:
            if any(attachment.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]):
                embed.set_image(url=attachment.url)
                break

    embed.set_footer(text=f"Quoted by {ctx.author.display_name}")
    await ctx.send(embed=embed)


# ============================================================
# DEVTEST MODE ISOLATION (DEVTEST / UNDEVTEST)
# ============================================================

@bot.command()
@moderator_only()
@commands.bot_has_permissions(manage_channels=True)
async def devtest(ctx):
    guild = ctx.guild
    guild_id_str = str(guild.id)

    if "devtest" not in data:
        data["devtest"] = {}

    if guild_id_str in data["devtest"]:
        existing_id = data["devtest"][guild_id_str]
        existing_channel = guild.get_channel(existing_id)
        if existing_channel:
            await ctx.send(
                f"Penny is already locked to devtest in {existing_channel.mention}!\n"
                f"Run `;undevtest` in that channel to unlock."
            )
            return

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

    test_channel = await guild.create_text_channel(
        name="pennyutils-devtest",
        overwrites=overwrites,
        topic="Temporary testing room for Penny. Use ;undevtest to delete.",
        reason="Devtest isolation initiated"
    )

    data["devtest"][guild_id_str] = test_channel.id
    save_data()

    await test_channel.send(
        f"🛠️ **Penny Devtest Activated**\n"
        f"The bot is now completely locked to this channel to prevent chat flood.\n"
        f"When testing is complete, run `{get_prefix(bot, ctx.message)}undevtest` here to delete this channel."
    )

    if ctx.channel.id != test_channel.id:
        await ctx.send(f"Created {test_channel.mention} and locked bot activity there! {EMOJI_BOYKISSER_HAPPY}")

@bot.command()
@moderator_only()
async def undevtest(ctx):
    guild = ctx.guild
    guild_id_str = str(guild.id)

    locked_channel_id = data.get("devtest", {}).get(guild_id_str)

    if not locked_channel_id:
        await ctx.send(f"This server is not currently in devtest mode! {EMOJI_BOYKISSER_HUH}")
        return

    locked_channel = guild.get_channel(locked_channel_id)

    if locked_channel is None:
        del data["devtest"][guild_id_str]
        save_data()
        await ctx.send("The devtest channel was already deleted. Devtest lockdown has been cleared! 🔓")
        return

    if ctx.channel.id != locked_channel_id:
        await ctx.send(f"You must run `;undevtest` inside the active devtest channel ({locked_channel.mention})! {EMOJI_BOYKISSER_HUH}")
        return

    del data["devtest"][guild_id_str]
    save_data()

    await ctx.send(f"Devtest mode ended. Deleting channel in 3 seconds... {EMOJI_DANCING}")
    await asyncio.sleep(3)
    try:
        await ctx.channel.delete(reason="Devtest session terminated.")
    except discord.HTTPException:
        pass


# ============================================================
# UTILITY
# ============================================================

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"Pong! `{latency}ms`")

@bot.command()
async def botinfo(ctx):
    embed = discord.Embed(
        title="Bot Information",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Version", value=f"`v{BOT_VERSION}`", inline=True)
    embed.add_field(name="Latency", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
    embed.add_field(name="Users", value=len(bot.users), inline=True)
    await ctx.send(embed=embed)


# ============================================================
# AUTOREPLY CONFIGURATION (DISABLED - REWORK SOON)
# ============================================================

@bot.group(invoke_without_command=True)
@owner_only()
async def autoreply(ctx):
    embed = discord.Embed(
        title="⚠️ Autoreply Feature Disabled",
        description="The automatic reply system is currently **disabled** and getting a rework soon!",
        color=discord.Color.orange()
    )
    embed.set_footer(text="Stay tuned for the upcoming update.")
    await ctx.send(embed=embed)

@autoreply.command(name="list")
@owner_only()
async def autoreply_list(ctx):
    await ctx.send("Autoreply is currently disabled for an upcoming rework.")

@autoreply.command(name="add")
@owner_only()
async def autoreply_add(ctx, *, text: str):
    await ctx.send("Autoreply is currently disabled for an upcoming rework.")

@autoreply.command(name="remove")
@owner_only()
async def autoreply_remove(ctx, index: int):
    await ctx.send("Autoreply is currently disabled for an upcoming rework.")

@autoreply.command(name="cooldown")
@owner_only()
async def autoreply_cooldown(ctx, seconds: int):
    await ctx.send("Autoreply is currently disabled for an upcoming rework.")


# ============================================================
# PREFIX CONFIGURATION
# ============================================================

@bot.command()
@owner_only()
async def prefix(ctx, new_prefix=None):
    if not new_prefix:
        await ctx.send(f"Current prefix: `{get_prefix(bot, ctx.message)}`")
        return

    if len(new_prefix) > 5:
        await ctx.send("The prefix cannot be longer than 5 characters.")
        return

    data["prefixes"][str(ctx.guild.id)] = new_prefix
    save_data()
    await ctx.send(f"Prefix changed to `{new_prefix}`.")


# ============================================================
# ERROR HANDLING
# ============================================================

@bot.command(aliases=["ap", "auto"])
async def autoplay(ctx):
    state = get_music_state(ctx.guild.id)
    state["autoplay"] = not state.get("autoplay", False)
    status = "enabled" if state["autoplay"] else "disabled"
    
    msg = f"📻 Autoplay is now **{status}**. "
    if state["autoplay"]:
        msg += f"When the queue ends, I will automatically play similar tracks! {EMOJI_DANCING}"
    else:
        msg += f"I will stop playing when the queue ends. {EMOJI_SHOCKED}"
        
    await ctx.send(msg)


@playlist.command(name="create")
async def playlist_create(ctx, *, name: str):
    is_server = "--server" in name
    clean_name = name.replace("--server", "").strip()

    if not clean_name:
        await ctx.send("Please specify a playlist name!")
        return

    if is_server:
        if not is_moderator(ctx.author.id):
            await ctx.send("Only server moderators can create server-wide playlists!")
            return
        g_pls = playlists_data["guilds"].setdefault(str(ctx.guild.id), {})
        if clean_name in g_pls:
            await ctx.send(f"A server playlist named **{clean_name}** already exists!")
            return
        g_pls[clean_name] = []
        save_playlists()
        await ctx.send(f"Created server playlist **{clean_name}**! 🌐 {EMOJI_BOYKISSER_HAPPY}")
    else:
        u_pls = playlists_data["users"].setdefault(str(ctx.author.id), {})
        if clean_name in u_pls:
            await ctx.send(f"You already have a playlist named **{clean_name}**!")
            return
        u_pls[clean_name] = []
        save_playlists()
        await ctx.send(f"Created personal playlist **{clean_name}**! 👤 {EMOJI_BOYKISSER_HAPPY}")


@playlist.command(name="add")
async def playlist_add(ctx, pl_name: str, *, query: str = None):
    is_server = False
    if query and "--server" in query:
        is_server = True
        query = query.replace("--server", "").strip()
    elif "--server" in pl_name:
        is_server = True
        pl_name = pl_name.replace("--server", "").strip()

    target_track = None
    state = get_music_state(ctx.guild.id)

    if query:
        loop = asyncio.get_event_loop()
        try:
            def _extract():
                with yt_dlp.YoutubeDL(YTDL_OPTS) as ydl:
                    return ydl.extract_info(query, download=False)
            data_info = await loop.run_in_executor(None, _extract)
            if 'entries' in data_info and data_info['entries']:
                entry = data_info['entries'][0]
                target_track = {'title': entry.get('title', 'Unknown Track'), 'webpage_url': entry.get('webpage_url') or entry.get('url')}
            else:
                target_track = {'title': data_info.get('title', 'Unknown Track'), 'webpage_url': data_info.get('webpage_url') or data_info.get('url')}
        except Exception as e:
            await ctx.send(f"Failed to lookup track: `{e}`")
            return
    elif state["current"]:
        target_track = state["current"]
    else:
        await ctx.send("No track specified or currently playing! Usage: `;playlist add <name> [query] [--server]`")
        return

    clean_title = sanitize_markdown(target_track["title"], max_len=60)
    track_item = {
        "title": clean_title,
        "url": target_track["webpage_url"],
        "added_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    if is_server:
        if not is_moderator(ctx.author.id):
            await ctx.send("Only server moderators can modify server playlists!")
            return
        g_pls = playlists_data["guilds"].get(str(ctx.guild.id), {})
        if pl_name not in g_pls:
            await ctx.send(f"Server playlist **{pl_name}** does not exist!")
            return
        g_pls[pl_name].append(track_item)
        save_playlists()
        await ctx.send(f"Added **{clean_title}** to server playlist **{pl_name}**! 🌐")
    else:
        u_pls = playlists_data["users"].get(str(ctx.author.id), {})
        if pl_name not in u_pls:
            await ctx.send(f"You don't have a playlist named **{pl_name}**! Create it first with `;playlist create {pl_name}`.")
            return
        u_pls[pl_name].append(track_item)
        save_playlists()
        await ctx.send(f"Added **{clean_title}** to your playlist **{pl_name}**! 👤")


@playlist.command(name="play")
async def playlist_play(ctx, pl_name: str, *, flag: str = ""):
    is_server = "--server" in flag or "--server" in pl_name
    pl_name = pl_name.replace("--server", "").strip()

    if is_server:
        tracks = playlists_data["guilds"].get(str(ctx.guild.id), {}).get(pl_name, [])
    else:
        tracks = playlists_data["users"].get(str(ctx.author.id), {}).get(pl_name, [])

    if not tracks:
        await ctx.send(f"Playlist **{pl_name}** is empty or doesn't exist!")
        return

    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send(f"You must be in a voice channel first! {EMOJI_BOYKISSER_HUH}")
        return

    voice_channel = ctx.author.voice.channel
    vc = ctx.guild.voice_client
    if not vc:
        vc = await voice_channel.connect()
    elif vc.channel != voice_channel:
        await vc.move_to(voice_channel)

    state = get_music_state(ctx.guild.id)
    state["text_channel"] = ctx.channel

    for item in tracks:
        state["queue"].append({
            "title": item["title"],
            "webpage_url": item["url"]
        })

    if not vc.is_playing() and not vc.is_paused():
        await play_next_track(ctx.guild.id)
        await ctx.send(f"Now playing playlist **{pl_name}** ({len(tracks)} tracks)! 🎶 {EMOJI_DANCING}")
    else:
        await ctx.send(f"Queued playlist **{pl_name}** ({len(tracks)} tracks)! 🎶 {EMOJI_BLUSH}")


@playlist.command(name="view")
async def playlist_view(ctx, pl_name: str, *, flag: str = ""):
    is_server = "--server" in flag or "--server" in pl_name
    clean_name = pl_name.replace("--server", "").strip()

    view = PlaylistView(ctx, clean_name, is_server=is_server)
    embed = view.get_embed()
    await ctx.send(embed=embed, view=view)


@playlist.command(name="list")
async def playlist_list(ctx, *, flag: str = ""):
    is_server = "--server" in flag
    if is_server:
        pls = playlists_data["guilds"].get(str(ctx.guild.id), {})
        title = "🌐 Server Playlists"
    else:
        pls = playlists_data["users"].get(str(ctx.author.id), {})
        title = "👤 Your Personal Playlists"

    embed = discord.Embed(title=title, color=discord.Color.blue())
    if not pls:
        embed.description = "No playlists found! Use `;playlist create <name>` to start one."
    else:
        desc = ""
        for name, tracks in pls.items():
            desc += f"• **{name}** (`{len(tracks)} track(s)`)\n"
        embed.description = desc

    await ctx.send(embed=embed)


@playlist.command(name="remove")
async def playlist_remove(ctx, pl_name: str, index: int, *, flag: str = ""):
    is_server = "--server" in flag or "--server" in pl_name
    pl_name = pl_name.replace("--server", "").strip()

    if is_server:
        if not is_moderator(ctx.author.id):
            await ctx.send("Only server moderators can modify server playlists!")
            return
        pls = playlists_data["guilds"].get(str(ctx.guild.id), {})
    else:
        pls = playlists_data["users"].get(str(ctx.author.id), {})

    if pl_name not in pls:
        await ctx.send(f"Playlist **{pl_name}** does not exist!")
        return

    tracks = pls[pl_name]
    if index < 1 or index > len(tracks):
        await ctx.send(f"Invalid song number! Please check `;playlist view {pl_name}`.")
        return

    removed = tracks.pop(index - 1)
    save_playlists()
    await ctx.send(f"Removed **{removed['title']}** from **{pl_name}**.")


@playlist.command(name="delete")
async def playlist_delete(ctx, pl_name: str, *, flag: str = ""):
    is_server = "--server" in flag or "--server" in pl_name
    pl_name = pl_name.replace("--server", "").strip()

    if is_server:
        if not is_moderator(ctx.author.id):
            await ctx.send("Only server moderators can delete server playlists!")
            return
        pls = playlists_data["guilds"].get(str(ctx.guild.id), {})
    else:
        pls = playlists_data["users"].get(str(ctx.author.id), {})

    if pl_name not in pls:
        await ctx.send(f"Playlist **{pl_name}** does not exist!")
        return

    del pls[pl_name]
    save_playlists()
    await ctx.send(f"Deleted playlist **{pl_name}**.")


# ============================================================
# EVENTS
# ============================================================

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Logged in as: {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Version: {BOT_VERSION}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 50)


@bot.event
async def on_voice_state_update(member, before, after):
    if member.id == bot.user.id:
        return

    for guild in bot.guilds:
        if guild.voice_client and guild.voice_client.channel:
            vc_channel = guild.voice_client.channel
            non_bots = [m for m in vc_channel.members if not m.bot]
            if len(non_bots) == 0:
                await schedule_disconnect(guild.id, delay=60)
            else:
                cancel_disconnect(guild.id)

@bot.event
async def on_message_edit(before, after):
    if after.guild is None or before.author.bot:
        return
    if (
        before.content == after.content
        and before.attachments == after.attachments
        and before.embeds == after.embeds
    ):
        return

    details = {
        "Channel": after.channel.mention,
        "Message ID": after.id,
        "Before": before.content or "[no text content]",
        "After": after.content or "[no text content]",
    }
    if before.attachments != after.attachments:
        details["Attachments"] = (
            f"Before: {', '.join(item.filename for item in before.attachments) or 'none'}\n"
            f"After: {', '.join(item.filename for item in after.attachments) or 'none'}"
        )
    if before.embeds != after.embeds:
        details["Embeds"] = f"Changed from {len(before.embeds)} embed(s) to {len(after.embeds)} embed(s)."
    await log_action(
        after.guild,
        "Message Edited",
        actor=after.author,
        details=details,
        color=discord.Color.blue(),
        timestamp=after.edited_at
    )

@bot.event
async def on_raw_message_edit(payload):
    if payload.cached_message is not None or payload.guild_id is None:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    raw_author = payload.data.get("author") or {}
    author_id = raw_author.get("id")
    if raw_author.get("bot"):
        return
    author = bot.get_user(int(author_id)) if author_id else None
    details = {
        "Channel ID": payload.channel_id,
        "Message ID": payload.message_id,
        "Before": "Previous content was not available in the bot's message cache.",
        "After": payload.data.get("content") or "[no text content]",
    }
    if author is None and author_id:
        details["Actor"] = f"<@{author_id}> (`{author_id}`)"
    await log_action(
        guild,
        "Message Edited (not cached)",
        actor=author,
        details=details,
        color=discord.Color.blue()
    )

@bot.event
async def on_raw_message_delete(payload):
    if payload.guild_id is None:
        return
    if payload.message_id in purge_log_suppression:
        purge_log_suppression.discard(payload.message_id)
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    message = payload.cached_message
    target_id = message.author.id if message else None
    actor = await find_message_delete_actor(
        guild,
        target_id=target_id,
        channel_id=payload.channel_id
    )
    details = {
        "Channel": getattr(message.channel, "mention", f"`{payload.channel_id}`") if message else f"`{payload.channel_id}`",
        "Message ID": payload.message_id,
        "Content": format_deleted_message(message) if message else "Message content was not available in the bot's cache.",
    }
    if actor is None:
        details["Actor"] = "Unknown (no matching Discord audit-log entry was available)."
    await log_action(
        guild,
        "Message Deleted",
        actor=actor,
        target=message.author if message else None,
        details=details,
        color=discord.Color.red(),
        timestamp=message.created_at if message else None
    )

@bot.event
async def on_raw_bulk_message_delete(payload):
    if payload.guild_id is None:
        return

    message_ids = set(payload.message_ids)
    suppressed_ids = message_ids & purge_log_suppression
    purge_log_suppression.difference_update(suppressed_ids)
    remaining_ids = message_ids - suppressed_ids
    if not remaining_ids:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    cached_messages = [
        message
        for message in payload.cached_messages
        if message.id in remaining_ids
    ]
    actor = await find_message_delete_actor(
        guild,
        channel_id=payload.channel_id,
        bulk=True,
        count=len(message_ids)
    )
    transcript = "\n".join(format_deleted_message(message) for message in cached_messages)
    if len(cached_messages) < len(remaining_ids):
        unavailable_count = len(remaining_ids) - len(cached_messages)
        transcript += (
            f"\n[{unavailable_count} message(s) were not cached; "
            f"IDs: {', '.join(str(message_id) for message_id in sorted(remaining_ids) if message_id not in {m.id for m in cached_messages})}]"
        )
    chunks = [
        transcript[index:index + 950]
        for index in range(0, len(transcript), 950)
    ] or ["No message content was available."]
    for index, chunk in enumerate(chunks, start=1):
        details = {
            "Channel ID": payload.channel_id,
            "Deleted message count": len(remaining_ids),
            "Message content": chunk,
        }
        if actor is None:
            details["Actor"] = "Unknown (no matching Discord audit-log entry was available)."
        await log_action(
            guild,
            "Messages Bulk Deleted" if index == 1 else f"Messages Bulk Deleted (continued {index})",
            actor=actor,
            details=details,
            color=discord.Color.red()
        )

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

# ============================================================
# ERROR HANDLING
# ============================================================

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    if isinstance(error, commands.CheckFailure):
        err_msg = str(error)

        if "BLACKLISTED" in err_msg:
            return

        if "SPAMMING" in err_msg:
            return

        if "OWNER_ONLY" in err_msg:
            await ctx.send("Only the bot developer is authorized to run this command.")
            return

        if "DISABLED_GLOBAL:" in err_msg:
            cmd = err_msg.split("DISABLED_GLOBAL:")[1].strip()
            await ctx.send(f"The `{cmd}` command has been temporarily disabled globally by the developer. {EMOJI_SHOCKED}")
            return

        if "DISABLED_SERVER:" in err_msg:
            cmd = err_msg.split("DISABLED_SERVER:")[1].strip()
            await ctx.send(f"The `{cmd}` command is currently disabled in this server. {EMOJI_SHOCKED}")
            return

        if "DEVTEST_LOCKED:" in err_msg:
            ch_id = err_msg.split("DEVTEST_LOCKED:")[1].strip()
            await ctx.send(
                f"🔒 **Command Blocked:** Penny is currently locked to <#{ch_id}> in devtest mode.\n"
                f"Please run commands inside that channel, or use `{get_prefix(bot, ctx.message)}undevtest` to unlock."
            )
            return

        await ctx.send("You are not authorized to use this command.")
        return

    if isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(f"`{p}`" for p in error.missing_permissions)
        await ctx.send(f"I don't have the Discord permissions required to perform that action: {missing}")
        return

    if isinstance(error, commands.MissingPermissions):
        missing = ", ".join(f"`{p}`" for p in error.missing_permissions)
        await ctx.send(f"You don't have the Discord permissions required to use that: {missing}")
        return

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: `{error.param.name}`")
        return

    if isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument provided. Please make sure your mentions, IDs, and numbers are correct.")
        return

    print(f"\n[Command Error in {ctx.command}]: {error}")
    traceback.print_exception(type(error), error, error.__traceback__)


# ============================================================
# START
# ============================================================

if not TOKEN:
    print("Error: No bot token found. Make sure your '.env' file is configured correctly.")
else:
    bot.run(TOKEN)