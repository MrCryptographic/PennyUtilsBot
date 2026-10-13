# PennyUtils

PennyUtils (Penny) is a Discord bot with moderation and server utilities, meme
generators, a local AI chat integration, and voice-channel music playback.

## Features

- Moderation tools with per-command moderation logs.
- Captioned meme GIFs and an interactive two-panel meme.
- Music search and playback, queue controls, audio filters, favorites, and
  personal or server playlists.
- Optional AI chat served locally by LM Studio.
- Persistent settings, warnings, playlists, favorites, and moderation data
  stored in local JSON files.

## Requirements

- Python 3.8 or later.
- FFmpeg installed and available on `PATH` for music playback.
- LM Studio running its local OpenAI-compatible server on port `1234` for AI
  chat (optional).
- A Discord bot application and token.

Install the Python dependencies:

```bash
pip install discord.py python-dotenv yt-dlp PyNaCl Pillow aiohttp
```

## Setup

1. Install the requirements above and make sure `ffmpeg` is available from your
   terminal.
2. Create a `.env` file in the project root:

   ```env
   TOKEN=your_discord_bot_token
   ```

   Keep this file private; do not commit your token.
3. In the Discord Developer Portal, enable the **Message Content Intent** (the
   bot uses prefix commands). The bot requests all Discord intents, so enable
   any privileged intents required by your application.
4. Keep the following meme templates in the `assets` folder:
   `basketball.gif`, `boykisser-leash.gif`, `fanumfood.gif`, `jarvis.gif`,
   `lockin.png`, `lowtiergod.gif`, `reason.gif`, `spongebob.gif`,
   `stephen.jpg`, `tryhard.gif`, and `tuffbob.gif`. The `impact.ttf` font is
   included in the project root; the bot also falls back to system fonts.
5. Start the bot:

   ```bash
   python bot.py
   ```

The default command prefix is `;`. The owner can change it per server with
`;prefix <new-prefix>`. Replace `;` in the examples below with the configured
prefix. Moderation and owner-only access are restricted to user IDs configured
in `bot.py`; being a Discord server moderator alone does not grant those
commands unless that ID is configured.

## Commands

Use `;help` in Discord for the paginated in-bot command menu.

### Moderation

These commands are restricted to the moderator IDs configured in `bot.py`.
Commands guarded by Discord permission checks also require Penny to have those
permissions.

| Command | Description |
| --- | --- |
| `;kick @member [reason]` | Kick a member. |
| `;ban @member [reason]` | Ban a member. |
| `;unban <user-id>` | Unban a user by ID. |
| `;timeout @member <minutes> [reason]` | Time out a member. |
| `;untimeout @member` | Remove a member's timeout. |
| `;warn @member [reason]` | Add a persistent warning. |
| `;warnings @member` | Show a member's warnings. |
| `;clearwarnings @member` | Clear a member's warnings. |
| `;purge <amount>` | Delete the requested number of recent messages. |
| `;slowmode <seconds>` | Set channel slowmode (0–21600 seconds). |
| `;lock` / `;unlock` | Disable or restore sending messages for the default role in this channel. |
| `;nick @member [nickname]` | Set or reset a member's nickname. |
| `;announce <message>` | Post an `@everyone` announcement embed. |
| `;devtest` / `;undevtest` | Create a temporary channel and restrict bot activity to it, then end the test and delete the channel. |

### Server and user utilities

| Command | Description |
| --- | --- |
| `;serverinfo` | Show server owner, member/channel/role counts, and server ID. |
| `;userinfo [@member]` | Show account and server-member details. Defaults to you. |
| `;avatar [@member]` | Show a member's avatar. Defaults to you. |
| `;banner [@member]` | Show a member's profile banner, if set. Defaults to you. |
| `;ping` | Show the bot's gateway latency. |
| `;botinfo` | Show bot version, latency, server count, and user count. |
| `;prefix [new-prefix]` | Show the current prefix or, for the owner, set this server's prefix. |
| `;quotethis` (alias: `;quote`) | Reply to a message with this command to quote its text and first image attachment. |

### Fun and interaction

| Command | Description |
| --- | --- |
| `;furry [@member]` | Show a deterministic-for-that-user furry percentage. |
| `;femboy [@member]` | Show a deterministic-for-that-user femboy percentage. |
| `;ship @member [@second-member]` (alias: `;match`) | Show a deterministic compatibility percentage. If the second member is omitted, ship yourself with the mentioned member. |
| `;kiss @member` | Send a playful kiss message. |
| `;hug @member` | Send a playful hug message. |
| `;punch @member` | Send a playful punch message. |
| `;attack @member` | Send a randomly chosen silly attack message. |
| `;boop @member` | Send a playful nose-boop message. |
| `;dance [@member]` | Dance alone or with a member. |

### Memes and quotes

Caption text is required unless noted. Caption commands render and send a GIF
using the matching image in `assets` (or the project root as a fallback).

| Command | Aliases | Description |
| --- | --- | --- |
| `;jarvis <text>` | — | Caption the Jarvis template. |
| `;lowtiergod <text>` | — | Caption the Low Tier God template. |
| `;spongebob <text>` | `;floating`, `;ascend`, `;sponge` | Caption the floating SpongeBob template. |
| `;tuffbob <text>` | `;tuff`, `;hoodiebob`, `;sadbob` | Caption the TuffBob template. |
| `;fanumfood <text>` | `;fanum`, `;food` | Caption the Fanum Food template. |
| `;stephen <text>` | `;pilot`, `;crossview` | Caption the Stephen template. |
| `;katanaman <text>` | `;reason`, `;heartbeats` | Caption the Katana Man template (`reason.gif`). |
| `;basketball <text>` | `;yaoming`, `;cried` | Caption the basketball/Yao Ming template. |
| `;tryhard <text>` | — | Caption the Tryhard template. |
| `;bkleash <text>` | — | Caption the Boykisser Leash template. |
| `;lockin <first caption> \| <second caption>` | — | Add separate captions to both panels of the Lock In image. |

### AI chat

The AI uses the locally hosted LM Studio server at
`http://localhost:1234/v1/chat/completions`. It is optional and must be running
for chat commands to work.

| Command | Description |
| --- | --- |
| `;chat <message>` (aliases: `;c`, `;ai`) | Chat with your selected AI persona. |
| `;persona [name]` | Show available personas, or select `default`, `jarvis`, `boykisser`, `lowtiergod`, `maid`, or `superuncensored`. Changing persona clears your current chat history. |
| `;clearchat` | Clear your current in-memory chat history. |

**Content warning:** The `superuncensored` persona may produce strong language
and offensive or otherwise inappropriate content. It is not suitable for all
audiences. Penny displays this warning before the first AI response after you
select that persona or clear your chat.

### Music

Music commands are for a server voice channel. The user invoking playback must
be in a voice channel; Penny also needs the required voice-channel permissions.

| Command | Aliases | Description |
| --- | --- | --- |
| `;play <search query or URL>` | `;p` | Play a search result or URL; playlist URLs are queued. |
| `;playfile` | — | Play one supported audio file attached to the command, or reply to a message containing that file and run `;playfile`; supported extensions: `.aac`, `.flac`, `.m4a`, `.mp3`, `.oga`, `.ogg`, `.opus`, `.wav`, `.webm`, and `.wma`. |
| `;join` | — | Join or move to your voice channel. |
| `;leave` | `;disconnect` | Disconnect and clear the current queue. |
| `;skip` | `;s`, `;next` | Skip the current track. |
| `;restartsong` | `;replay` | Replay the current track. |
| `;pause` / `;resume` | — | Pause or resume playback. |
| `;stop` | — | Stop playback and clear the queue. |
| `;queue` | `;q` | Open the interactive queue (pause/resume, skip, shuffle, clear, and page controls). |
| `;nowplaying` | `;np` | Show the current track and interactive player controls. |
| `;volume [1-100]` | `;vol` | Show or set playback volume. |
| `;loop` | — | Toggle looping of the current track. |
| `;effect [name]` | `;effects`, `;filter` | Open the effect menu or set `none`, `reverb`, `bassboost`, `nightcore`, `vaporwave`, `8d`, or `echo`. |
| `;autorestart` | `;autorestartfx`, `;autorestarteffect` | Toggle restarting the current track when an effect changes. |
| `;autoplay` | `;ap`, `;auto` | Toggle automatic related-track playback when the queue ends. |
| `;favorite [search query or URL]` | `;fav` | Save the current track, or look up and save a supplied track. Favorites are saved to both this server and your personal list. |
| `;favorites` | `;favs` | Open the interactive server/personal favorites manager. |

### Playlists

Use `;playlist` (aliases: `;pl`, `;playlists`) to show playlist syntax. Playlists
are personal by default. Add `--server` to use a server-wide playlist; only
configured moderators can create or change server playlists.

| Command | Description |
| --- | --- |
| `;playlist create <name> [--server]` | Create a personal or server playlist. |
| `;playlist add <name> [search query or URL] [--server]` | Add the supplied track, or the currently playing track when omitted. |
| `;playlist play <name> [--server]` | Queue and play a playlist. |
| `;playlist list [--server]` | List your personal or server playlists. |
| `;playlist view <name> [--server]` | View tracks with an interactive play control. |
| `;playlist remove <name> <track-number> [--server]` | Remove a track (track numbers start at 1). |
| `;playlist delete <name> [--server]` | Delete a playlist. |

### Owner-only administration

These commands are available only to the owner IDs configured in `bot.py`.

| Command | Description |
| --- | --- |
| `;setlog #channel` | Set the server's moderation-log destination. |
| `;disablelog` | Turn off moderation logging for this server. |
| `;disable <command> [--global]` | Disable a command in this server, or globally when `--global` is provided. |
| `;enable <command> [--global]` | Re-enable a command in this server, or globally when `--global` is provided. |
| `;blacklist add @user [command]` | Block a user from all commands, or from one command. |
| `;blacklist remove @user [command]` | Remove a full or command-specific block. |
| `;blacklist list` | Show the configured blacklist. |
| `;restart` | Save persistent data and restart the bot process. |

The owner-only `;autoreply` group and its `;autoreply list`,
`;autoreply add <text>`, `;autoreply remove <index>`, and
`;autoreply cooldown <seconds>` subcommands are currently disabled; they only
report that the feature is unavailable.

## Data and privacy

Bot settings, moderation warnings, and devtest state are stored in
`bot_data.json`; favorites and playlists are stored in `favorites.json` and
`playlists.json`. AI prompts are sent to the locally configured LM Studio
endpoint, not to a hosted AI API by this code. Discord command interactions
still pass through Discord, and AI chat history is kept in bot memory only
while the bot process is running.
