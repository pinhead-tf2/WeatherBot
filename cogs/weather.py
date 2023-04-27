import discord
import aiohttp
import re

from datetime import datetime, timezone
from discord.commands import SlashCommandGroup
from discord.ext import commands
from images.image_report import generate_image


async def urlify(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '+', s)
    # thank you Kenan Banks
    # https://stackoverflow.com/a/1007615
    return s


async def determine_color(report):
    alerts = report['alerts']
    active_alert = False if len(alerts['alert']) == 0 else True
    print(active_alert)
    # weather_code = report['current']['condition']['code']  # current condition's code
    weather_code = report['forecast']['forecastday'][0]['day']['condition']['code']  # current day's overall forecast code
    is_day = report['current']['is_day']

    if active_alert:
        return discord.Color.red()
    elif weather_code == 1000 and is_day == 1:  # clear and day
        return 0xcad3f5  # barely grey
    elif weather_code == 1000 and is_day == 0:  # clear and night
        return 0x313c76  # dark blue

    match weather_code:
        # clouds/sky
        case 1003:  # partly cloudy
            return 0x939ab7  # light grey
        case 1006:  # cloudy
            return 0x6e738d  # medium grey
        case 1009:  # overcast
            return 0x494d64  # dark grey
        case 1030 | 1063:  # mist, patchy rain possible
            return 0xe4fcdc  # very light green

        # rain
        case 1150 | 1153 | 1180 | 1183 | 1240:  # patchy light drizzle, light drizzle, patchy light rain, light rain,
            # light rain shower
            return 0xa6da95  # light green
        case 1186 | 1189 | 1273 | 1087:  # moderate rain at times, moderate rain, patchy light rain with thunder,
            # thundery outbreaks possible
            return 0x90ff6c  # green
        case 1192 | 1195:  # heavy rain at times, heavy rain
            return 0x5ede34  # dark green
        case 1246 | 1276:  # torrential rain shower, moderate or heavy rain with thunder
            return 0x40a02b  # very dark green

        # snow/ice pellets
        case 1135 | 1210 | 1213 | 1255 | 1261 | 1279:  # patchy light snow with thunder, patchy light snow, light snow,
            # light showers of ice pellets, light snow showers
            return 0xcae2fe  # very light blue
        case 1114 | 1216 | 1219 | 1237:  # blowing snow, patchy moderate snow, moderate snow, ice pellets
            return 0xb7bdf8  # light blue
        case 1222 | 1225 | 1258 | 1264 | 1282:  # patchy heavy snow, heavy snow, moderate or heavy snow showers,
            # moderate or heavy showers of ice pellets, moderate or heavy snow with thunder
            return 0x8aadf4  # blue
        case 1117 | 1147:  # blizzard, freezing fog
            return 0x5483e2  # dark blue

        # sleet/freezing
        case 1069 | 1072 | 1198 | 1204 | 1249:  # patchy sleet possible, patchy freezing drizzle possible,
            # light freezing rain, light sleet, light sleet showers
            return 0xffd8f5  # light pink
        case 1168:  # freezing drizzle
            return 0xf5bde6  # lightish pink
        case 1171, 1201, 1207:  # heavy freezing drizzle, moderate or heavy freezing rain, moderate or heavy sleet
            return 0xf977d7  # pink
        case _:
            return 0x000000


async def will_it_weather(likeliness):
    return 'Yes' if likeliness == 1 else 'No'


class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def current_forecast_weather(self, location: str):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.weatherapi.com/v1/forecast.json',
                                   params={"key": self.bot.WEATHER_TOKEN,
                                           "q": location,
                                           "alerts": "yes"
                                           }) as response:
                return await response.json()

    weather = SlashCommandGroup("weather", "Gets weather at a location")

    @weather.command()
    async def current(self, ctx, city: discord.Option(str), image: discord.Option(bool)):
        report_current = await self.current_forecast_weather(city)

        if image:
            image = generate_image(report_current)
            await ctx.respond(file=image)
        else:
            # ease of access, yknow?
            location = report_current['location']
            current = report_current['current']
            condition = current['condition']
            forecast = report_current['forecast']
            forecast_today = forecast['forecastday'][0]['day']  # this is what it takes to get today's chance of rain
            rain_chance = forecast_today['daily_chance_of_rain']
            rain_likely = await will_it_weather(forecast_today['daily_will_it_rain'])
            snow_chance = forecast_today['daily_chance_of_snow']
            snow_likely = await will_it_weather(forecast_today['daily_will_it_snow'])

            embed = discord.Embed(title=f"{location['name']}, "f"{location['region']}",
                                  description=location['country'],
                                  url=f"https://www.google.com/maps/search/?api=1&query="
                                      f"{await urlify(location['name'])}%2C"
                                      f"{await urlify(location['region'])}%2C"
                                      f"{await urlify(location['country'])}",
                                  timestamp=datetime.now(timezone.utc),
                                  color=await determine_color(report_current)
                                  )
            timestring = datetime.fromtimestamp(current['last_updated_epoch']).strftime("%I:%M %p")
            embed.set_footer(text=f"Data as of {timestring} | Source: WeatherAPI.com")
            embed.set_thumbnail(url=f"https:{condition['icon']}")
            embed.add_field(name="Temperature",
                            value=f"*Current:* {current['temp_f']}°F\n"
                                  f"*Low/High:* {forecast_today['mintemp_f']}°F/{forecast_today['maxtemp_f']}°F",
                            inline=True)
            embed.add_field(name="Condition",
                            value=f"{condition['text']}\n"
                                  f"*Humidity:* {current['humidity']}%",
                            inline=True)
            embed.add_field(name='\u200b', value='\u200b', inline=True)  # ensure 2 line embed

            if snow_chance == 0 and current['temp_f'] > 35:
                embed.add_field(name='Precipitation',
                                value=f"*Chance of Rain:* {rain_chance}%\n"
                                      f"*Likely to Rain:* {rain_likely}",
                                inline=True)
            elif snow_chance > 0 and rain_chance > 0:
                embed.add_field(name='Precipitation',
                                value=f"*Chance of Rain:* {rain_chance}%\n"
                                      f"*Likely to Rain:* {rain_likely}"
                                      f"*Chance of Snow:* {snow_chance}%\n"
                                      f"*Likely to Snow:* {snow_likely}",
                                inline=True)
            else:
                embed.add_field(name='Precipitation',
                                value=f"*Chance of Snow:* {snow_chance}%\n"
                                      f"*Likely to Snow:* {snow_likely}",
                                inline=True)
            await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Weather(bot))
