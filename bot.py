import discord
from discord.ext import commands
from discord import app_commands
import re
from collections import Counter

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"บอท {bot.user} ออนไลน์แล้ว! (เวอร์ชันนับทั้ง +1 และ -1 ทุกห้อง)")

# 1. คำสั่ง /vouch @ชื่อคนนั้น (นับทั้ง +1 และ -1)
@bot.tree.command(name="vouch", description="เช็กเครดิตความน่าเชื่อถือ (+1 และ -1) ของสมาชิก")
@app_commands.describe(member="เลือกสมาชิกที่ต้องการดูเครดิต")
async def vouch(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer()

    plus_count = 0
    minus_count = 0
    target_id = str(member.id)

    for channel in interaction.guild.text_channels:
        try:
            async for message in channel.history(limit=5000):
                if message.author.bot or str(message.author.id) == target_id:
                    continue

                if re.search(rf"<@!?{target_id}>\s*\+1|\+1\s*<@!?{target_id}>", message.content):
                    plus_count += 1
                elif re.search(rf"<@!?{target_id}>\s*-1|-1\s*<@!?{target_id}>", message.content):
                    minus_count += 1
        except discord.Forbidden:
            continue

    net_score = plus_count - minus_count

    embed = discord.Embed(
        title=f"เครดิตความน่าเชื่อถือของ {member.display_name}",
        description=(
            f"สรุปประวัติการรับรองจากสมาชิกในเซิร์ฟเวอร์:\n\n"
            f"⭐ ได้รับการรับรอง (+1): **{plus_count} ครั้ง**\n"
            f"🔻 โดนหักเครดิต (-1): **{minus_count} ครั้ง**\n"
            f"🏆 เครดิตสุทธิ: **{net_score} คะแนน**"
        ),
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    
    guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
    embed.set_footer(text=f"{interaction.guild.name} Vouch System", icon_url=guild_icon)

    await interaction.followup.send(embed=embed)

# 2. คำสั่ง /topvouches (จัดอันดับ Top 10 จากคะแนนสุทธิ)
@bot.tree.command(name="topvouches", description="แสดงตารางจัดอันดับความน่าเชื่อถือ 10 อันดับแรก")
async def topvouches(interaction: discord.Interaction):
    await interaction.response.defer()

    scores = Counter()

    for channel in interaction.guild.text_channels:
        try:
            async for message in channel.history(limit=5000):
                if message.author.bot:
                    continue

                plus_matches = re.findall(r"<@!?(\d+)>\s*\+1|\+1\s*<@!?(\d+)>", message.content)
                for m in plus_matches:
                    target_id = m[0] or m[1]
                    if target_id != str(message.author.id):
                        scores[target_id] += 1

                minus_matches = re.findall(r"<@!?(\d+)>\s*-1|-1\s*<@!?(\d+)>", message.content)
                for m in minus_matches:
                    target_id = m[0] or m[1]
                    if target_id != str(message.author.id):
                        scores[target_id] -= 1
        except discord.Forbidden:
            continue

    top_10 = scores.most_common(10)
    medals = ["🥇", "🥈", "🥉"]
    lines = []

    for index, (user_id, score) in enumerate(top_10):
        rank_prefix = medals[index] if index < 3 else f"**#{index + 1}**"
        lines.append(f"{rank_prefix} <@{user_id}> — **{score} Vouches**")

    description_text = "\n\n".join(lines) if lines else "ยังไม่มีข้อมูลเครดิตในเซิร์ฟเวอร์"

    embed = discord.Embed(
        title="🏆 ตารางจัดอันดับความน่าเชื่อถือ (Top Vouches)",
        description=description_text,
        color=discord.Color.gold()
    )

    guild_icon = interaction.guild.icon.url if interaction.guild.icon else None
    embed.set_thumbnail(url=guild_icon)
    embed.set_footer(text=f"{interaction.guild.name} Vouch System", icon_url=guild_icon)

    await interaction.followup.send(embed=embed)

bot.run(os.environ.get("TOKEN"))