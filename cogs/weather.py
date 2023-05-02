import discord
import aiohttp
import re

from io import BytesIO
from datetime import datetime, timezone
from catppuccin import Flavour
from discord import option
from discord.commands import SlashCommandGroup
from discord.ext import commands
from images.image_report import generate_image, determine_outlook


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
        return Flavour.mocha().maroon.rgba
    elif weather_code == 1000 and is_day == 1:  # clear and day
        return Flavour.mocha().rosewater.rgba  # barely grey
    elif weather_code == 1000 and is_day == 0:  # clear and night
        return Flavour.mocha().overlay0.rgba  # dark blue

    outlook, colors = determine_outlook(weather_code)
    return colors


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

    @weather.command(name="current", description="Gets the current weather at a given location")
    @option("location", str, description="The desired location to get the weather from. "
                                         "Use a city name or postal code.")
    @option("image", bool, description="Choose if you want to view the report as a generated image, or as an embed")
    async def current(self, ctx, location: str, image: discord.Option(bool)):
        report_current = await self.current_forecast_weather(location)

        if image:
            await ctx.defer()
            with BytesIO() as image_binary:
                generate_image(report_current).save(image_binary, 'PNG')
                image_binary.seek(0)
                await ctx.respond(file=discord.File(fp=image_binary, filename='report.png'))
        else:
            # ease of access, yknow?
            location = report_current['location']
            current = report_current['current']
            condition = current['condition']
            forecast = report_current['forecast']
            forecast_today = forecast['forecastday'][0]['day']  # this is what it takes to get today's chance of rain
            rain_chance = forecast_today['daily_chance_of_rain']
            rain_likely = 'Yes' if forecast_today['daily_will_it_rain'] == 1 else 'No'
            snow_chance = forecast_today['daily_chance_of_snow']
            snow_likely = 'Yes' if forecast_today['daily_will_it_snow'] == 1 else 'No'

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
