"""
Discord Bot - Türkçe Hava Durumu Botu
=====================================

Bu bot İstanbul ve diğer şehirlerin hava durumunu gösterir.

KURULUM:
1. Discord Developer Portal'a gidin: https://discord.com/developers/applications/
2. Yeni bir uygulama oluşturun ve Bot sekmesine gidin
3. Bot token'ını kopyalayın ve DISCORD_BOT_TOKEN secret'ına ekleyin
4. OpenWeatherMap'ten API anahtarı alın: https://openweathermap.org/api
5. API anahtarını WEATHER_API_KEY secret'ına ekleyin

PREFIX KOMUTLARI İÇİN (opsiyonel):
1. Discord Developer Portal > Bot > Privileged Gateway Intents
2. "Message Content Intent" seçeneğini etkinleştirin  
3. Replit Secrets'a ENABLE_PREFIX_COMMANDS=true ekleyin

KOMUTLAR:
• !ping - Bot'un yanıt süresini test eder
• !sunucu - Sunucu üye sayısını gösterir  
• !hava durumu şehir - Şehrin hava durumunu gösterir
• /ping - Slash versiyonu (her zaman çalışır)
• /sunucu - Slash versiyonu (her zaman çalışır)
• /hava-durumu - Slash versiyonu (her zaman çalışır)
"""

import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Load environment variables
load_dotenv()

# Bot configuration
intents = discord.Intents.default()
intents.guilds = True

# Enable message content intent if user wants prefix commands
# Set ENABLE_PREFIX_COMMANDS=true in environment to enable prefix commands
# You must also enable "Message Content Intent" in Discord Developer Portal
enable_prefix = os.getenv('ENABLE_PREFIX_COMMANDS', 'false').lower() == 'true'
if enable_prefix:
    intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Simple health check server for UptimeRobot monitoring
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Bot is running!')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Disable logging to reduce console spam
        pass

def start_health_server():
    """Start HTTP server for health checks on port 5000"""
    try:
        server = HTTPServer(('0.0.0.0', 5000), HealthCheckHandler)
        print("✅ Health check server started on port 5000")
        server.serve_forever()
    except Exception as e:
        print(f"⚠️ Health check server error: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} olarak giriş yapıldı!')
    print(f'Bot {len(bot.guilds)} sunucuda aktif')
    print('---')
    print('KOMUTlar:')
    print('• Prefix komutları: !ping, !sunucu, !hava durumu şehir')
    print('• Slash komutları: /ping, /sunucu, /hava-durumu')
    print('---')
    if bot.intents.message_content:
        print('✅ Message Content Intent etkin - prefix komutları çalışacak')
    else:
        print(
            '⚠️ Message Content Intent kapalı - sadece slash komutları çalışacak'
        )
        print(
            'Discord Developer Portal\'da Message Content Intent\'i etkinleştirin'
        )
    print('---')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'{len(synced)} slash komut senkronize edildi')
    except Exception as e:
        print(f'Slash komutlar senkronize edilemedi: {e}')


@bot.command(name='ping')
async def ping(ctx):
    """Bot'un yanıt verme süresini test eder"""
    await ctx.send('Pong!')


@bot.command(name='sunucu')
async def sunucu(ctx):
    """Sunucu bilgilerini gösterir"""
    guild = ctx.guild
    if guild:
        member_count = guild.member_count
        await ctx.send(f'Bu sunucuda **{member_count}** üye bulunuyor.')
    else:
        await ctx.send('Bu komut sadece sunucularda kullanılabilir.')


@bot.command(name='hava')
async def hava_durumu(ctx, durumu=None, sehir=None):
    """Hava durumu bilgisi getirir: !hava durumu İstanbul"""

    if durumu != 'durumu' or not sehir:
        await ctx.send(
            'Kullanım: `!hava durumu şehir_adı`\nÖrnek: `!hava durumu İstanbul`'
        )
        return

    # OpenWeatherMap API anahtarı
    api_key = os.getenv('WEATHER_API_KEY')
    if not api_key:
        await ctx.send(
            'Hava durumu servisi şu anda kullanılamıyor. API anahtarı bulunamadı.'
        )
        return

    try:
        # Weather API request
        url = f"http://api.openweathermap.org/data/2.5/weather?q={sehir}&appid={api_key}&units=metric&lang=tr"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            # Weather data extraction
            sehir_adi = data['name']
            sicaklik = data['main']['temp']
            hissedilen = data['main']['feels_like']
            nem = data['main']['humidity']
            aciklama = data['weather'][0]['description']
            ruzgar = data['wind']['speed'] if 'wind' in data else 'Bilinmiyor'

            # Create weather embed
            embed = discord.Embed(title=f"🌤️ {sehir_adi} Hava Durumu",
                                  color=0x87CEEB)
            embed.add_field(name="🌡️ Sıcaklık",
                            value=f"{sicaklik:.1f}°C",
                            inline=True)
            embed.add_field(name="🤚 Hissedilen",
                            value=f"{hissedilen:.1f}°C",
                            inline=True)
            embed.add_field(name="💧 Nem", value=f"%{nem}", inline=True)
            embed.add_field(name="☁️ Durum",
                            value=aciklama.capitalize(),
                            inline=True)
            embed.add_field(name="💨 Rüzgar",
                            value=f"{ruzgar} m/s",
                            inline=True)

            await ctx.send(embed=embed)

        elif response.status_code == 404:
            await ctx.send(
                f'❌ "{sehir}" şehri bulunamadı. Şehir adını kontrol edin.')
        else:
            await ctx.send(
                '❌ Hava durumu bilgisi alınamadı. Lütfen daha sonra tekrar deneyin.'
            )

    except requests.exceptions.RequestException:
        await ctx.send(
            '❌ Hava durumu servisine bağlanılamadı. İnternet bağlantınızı kontrol edin.'
        )
    except Exception as e:
        await ctx.send('❌ Beklenmeyen bir hata oluştu.')
        print(f"Hata: {e}")


# Slash Commands (Alternative to prefix commands)
@bot.tree.command(name="ping",
                  description="Bot'un yanıt verme süresini test eder")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message('Pong!')


@bot.tree.command(name="sunucu", description="Sunucu bilgilerini gösterir")
async def slash_sunucu(interaction: discord.Interaction):
    guild = interaction.guild
    if guild:
        member_count = guild.member_count
        await interaction.response.send_message(
            f'Bu sunucuda **{member_count}** üye bulunuyor.')
    else:
        await interaction.response.send_message(
            'Bu komut sadece sunucularda kullanılabilir.')


@bot.tree.command(name="hava-durumu",
                  description="Şehir için hava durumu bilgisi getirir")
async def slash_hava_durumu(interaction: discord.Interaction, sehir: str):
    # OpenWeatherMap API anahtarı
    api_key = os.getenv('WEATHER_API_KEY')
    if not api_key:
        await interaction.response.send_message(
            'Hava durumu servisi şu anda kullanılamıyor. API anahtarı bulunamadı.'
        )
        return

    await interaction.response.defer()  # Thinking...

    try:
        # Weather API request
        url = f"http://api.openweathermap.org/data/2.5/weather?q={sehir}&appid={api_key}&units=metric&lang=tr"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            # Weather data extraction
            sehir_adi = data['name']
            sicaklik = data['main']['temp']
            hissedilen = data['main']['feels_like']
            nem = data['main']['humidity']
            aciklama = data['weather'][0]['description']
            ruzgar = data['wind']['speed'] if 'wind' in data else 'Bilinmiyor'

            # Create weather embed
            embed = discord.Embed(title=f"🌤️ {sehir_adi} Hava Durumu",
                                  color=0x87CEEB)
            embed.add_field(name="🌡️ Sıcaklık",
                            value=f"{sicaklik:.1f}°C",
                            inline=True)
            embed.add_field(name="🤚 Hissedilen",
                            value=f"{hissedilen:.1f}°C",
                            inline=True)
            embed.add_field(name="💧 Nem", value=f"%{nem}", inline=True)
            embed.add_field(name="☁️ Durum",
                            value=aciklama.capitalize(),
                            inline=True)
            embed.add_field(name="💨 Rüzgar",
                            value=f"{ruzgar} m/s",
                            inline=True)

            await interaction.followup.send(embed=embed)

        elif response.status_code == 404:
            await interaction.followup.send(
                f'❌ "{sehir}" şehri bulunamadı. Şehir adını kontrol edin.')
        else:
            await interaction.followup.send(
                '❌ Hava durumu bilgisi alınamadı. Lütfen daha sonra tekrar deneyin.'
            )

    except requests.exceptions.RequestException:
        await interaction.followup.send(
            '❌ Hava durumu servisine bağlanılamadı. İnternet bağlantınızı kontrol edin.'
        )
    except Exception as e:
        await interaction.followup.send('❌ Beklenmeyen bir hata oluştu.')
        print(f"Hata: {e}")


@bot.event
async def on_command_error(ctx, error):
    """Hata yakalama"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            '❌ Geçersiz komut. `!ping`, `!sunucu` veya `!hava durumu şehir` komutlarını kullanabilirsiniz.'
        )
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Eksik parametre. Komut kullanımını kontrol edin.')
    else:
        print(f"Hata: {error}")


# Bot token
def main():
    # Start health check server in background thread for UptimeRobot monitoring
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        print("❌ DISCORD_BOT_TOKEN çevre değişkeni bulunamadı!")
        print("Lütfen .env dosyasında DISCORD_BOT_TOKEN'i ayarlayın.")
        # Replit Secrets'ta TOKEN kullandıysanız, burayı da kontrol edin.
        return

    try:
        bot.run(bot_token)
    except discord.LoginFailure:
        print("❌ Geçersiz bot token!")
    except Exception as e:
        print(f"❌ Bot başlatılırken hata oluştu: {e}")


if __name__ == '__main__':
    main()
