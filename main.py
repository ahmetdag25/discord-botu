import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv

# .env dosyasındaki değişkenleri yükle
load_dotenv()

# Bot Token'ı ve API anahtarlarını ortam değişkenlerinden al
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# İzinleri (Intents) tanımla
# Message Content Intent'i kapatarak sadece Slash komutlarına odaklanıyoruz
# (Bu, Render ve Discord için daha güvenli ve stabildir)
intents = discord.Intents.default()
intents.guilds = True  # Sunucu listesini görebilmek için

# Botu Slash Komutları için başlat
bot = commands.Bot(command_prefix='/', intents=intents)

# ----------------------------------------------------------------------
# Bot Olayları
# ----------------------------------------------------------------------

@bot.event
async def on_ready():
    """Bot Discord'a bağlandığında çalışır."""
    print('-------------------------------------')
    print(f'✅ Bot başarıyla giriş yaptı: {bot.user}')
    print(f'✅ Bot {len(bot.guilds)} sunucuda aktif')
    print('-------------------------------------')
    
    # Slash komutlarını senkronize et (Bot ilk çalıştığında bir kez yapar)
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} slash komut senkronize edildi.')
    except Exception as e:
        print(f'❌ Slash komutları senkronize edilemedi: {e}')


# ----------------------------------------------------------------------
# Slash Komutları
# ----------------------------------------------------------------------

@bot.tree.command(name="ping", description="Botun yanıt verme süresini test eder")
async def slash_ping(interaction: discord.Interaction):
    """/ping komutu"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'Pong! Gecikme süresi: {latency}ms')


@bot.tree.command(name="sunucu", description="Sunucu üye sayısını gösterir")
async def slash_sunucu(interaction: discord.Interaction):
    """/sunucu komutu"""
    guild = interaction.guild
    if guild:
        member_count = guild.member_count
        await interaction.response.send_message(
            f'Bu sunucuda **{member_count}** üye bulunuyor.')
    else:
        await interaction.response.send_message(
            'Bu komut sadece sunucularda kullanılabilir.')


@bot.tree.command(name="hava", description="Belirtilen şehir için hava durumu bilgisi getirir")
async def slash_hava(interaction: discord.Interaction, sehir: str):
    """/hava şehir_adı komutu"""
    
    if not WEATHER_API_KEY:
        await interaction.response.send_message(
            '❌ Hava durumu servisi şu anda kullanılamıyor. API anahtarı eksik.', 
            ephemeral=True) # Ephemeral: Sadece komutu kullanan görür
        return

    await interaction.response.defer()  # Cevap gelene kadar "düşünüyor..." göster

    try:
        # OpenWeatherMap API isteği
        url = f"http://api.openweathermap.org/data/2.5/weather?q={sehir}&appid={WEATHER_API_KEY}&units=metric&lang=tr"
        response = requests.get(url)
        data = response.json()

        if response.status_code == 200:
            # Hava durumu verilerini çıkar
            sehir_adi = data['name']
            sicaklik = data['main']['temp']
            hissedilen = data['main']['feels_like']
            nem = data['main']['humidity']
            aciklama = data['weather'][0]['description']
            ruzgar = data['wind']['speed'] if 'wind' in data else 'Bilinmiyor'

            # Embed oluştur
            embed = discord.Embed(title=f"🌤️ {sehir_adi} Hava Durumu",
                                  color=0x87CEEB)
            embed.add_field(name="🌡️ Sıcaklık", value=f"{sicaklik:.1f}°C", inline=True)
            embed.add_field(name="🤚 Hissedilen", value=f"{hissedilen:.1f}°C", inline=True)
            embed.add_field(name="💧 Nem", value=f"%{nem}", inline=True)
            embed.add_field(name="☁️ Durum", value=aciklama.capitalize(), inline=True)
            embed.add_field(name="💨 Rüzgar", value=f"{ruzgar} m/s", inline=True)
            embed.set_footer(text="Veriler OpenWeatherMap tarafından sağlanmıştır.")

            await interaction.followup.send(embed=embed) # Cevabı gönder

        elif response.status_code == 404:
            await interaction.followup.send(
                f'❌ **"{sehir}"** şehri bulunamadı. Şehir adını kontrol edin.')
        else:
            await interaction.followup.send(
                '❌ Hava durumu bilgisi alınamadı. API yanıtını kontrol edin.')

    except requests.exceptions.RequestException:
        await interaction.followup.send(
            '❌ Hava durumu servisine bağlanılamadı. Bağlantı hatası.')
    except Exception as e:
        await interaction.followup.send('❌ Beklenmeyen bir hata oluştu.')
        print(f"Hata: {e}")


# ----------------------------------------------------------------------
# Botu Başlatma
# ----------------------------------------------------------------------

if __name__ == '__main__':
    if not DISCORD_TOKEN:
        print("❌ HATA: DISCORD_BOT_TOKEN ortam değişkeni bulunamadı!")
        print("Lütfen Render ayarlarında bu değişkeni doğru eklediğinizden emin olun.")
    else:
        try:
            bot.run(DISCORD_TOKEN)
        except discord.LoginFailure:
            print("❌ HATA: Geçersiz Bot Token! Lütfen token'ı kontrol edin.")
        except Exception as e:
            print(f"❌ Bot başlatılırken genel bir hata oluştu: {e}")
