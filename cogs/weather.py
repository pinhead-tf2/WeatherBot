import discord
import aiohttp
import re

from datetime import datetime, timezone
from discord.commands import SlashCommandGroup
from discord.ext import commands


async def urlify(s):
    # Remove all non-word characters (everything except numbers and letters)
    s = re.sub(r"[^\w\s]", '', s)
    # Replace all runs of whitespace with a single dash
    s = re.sub(r"\s+", '+', s)
    # thank you Kenan Banks
    # https://stackoverflow.com/a/1007615
    return s


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
                if response.headers["CDN-Cache"] == "MISS":
                    print("hell")
                return await response.json()

    # https://www.weatherapi.com/docs/weather_conditions.json
    # color coding based on conditions
    # cloud cover is greys
    # rain is greens
    # snow is light blues
    # freezing is dark blues
    # sleet is pinks
    #
    # Red if alerts (the highest priority)
    #
    # clouds
    # 1000 = sunny = sky blue
    # 1003 = partly cloudy = light grey
    # 1006 = cloudy = med gray
    # 1009 = overcast = dark grey
    # 1000 = clear = slightly blue black
    #
    # rain
    # 1030, 1063 = mist, patchy rain possible = barely light green
    # 1150, 1153, 1180, 1183, 1240 = patchy light drizzle, light drizzle, patchy light rain, light rain, light rain shower = light green
    # 1186, 1189, 1273, 1087 = moderate rain at times, moderate rain, patchy light rain with thunder, thundery outbreaks possible = green
    # 1192, 1195 = heavy rain at times, heavy rain = darkish green
    # 1246, 1276 = torrential rain shower, moderate or heavy rain with thunder = dark green
    #
    # snow
    # 1210, 1213, 1255, 1279, 1135 = patchy light snow, light snow, light snow showers, patchy light snow with thunder = bright white
    # 1216, 1219 = patchy moderate snow, moderate snow = slightly blue white
    # 1222, 1225, 1258, 1282 = patchy heavy snow, heavy snow, moderate or heavy snow showers, moderate or heavy snow with thunder = notably blue white
    #
    # sleet
    # 1069 = patchy sleet possible = slightly pink


    async def determine_color(self, ctx, report):
        alerts = report['alerts']
        print(len(alerts['alert']))
        active_alert = False if len(alerts['alert']) == 0 else True
        if active_alert:
            return discord.Color.red()

        # switch

        return 000000

    weather = SlashCommandGroup("weather", "Gets weather at a location")

    @weather.command()
    async def current(self, ctx, city: discord.Option(str)):
        report_current = await self.current_forecast_weather(city)

        # ease of access, yknow?
        location = report_current['location']
        current = report_current['current']
        condition = current['condition']
        forecast = report_current['forecast']
        forecast_today = forecast['forecastday'][0]['day']  # this is what it takes to get today's chance of rain
        rain_chance = forecast_today['daily_chance_of_rain']
        snow_chance = forecast_today['daily_chance_of_snow']

        embed = discord.Embed(title=f"{location['name']}, "f"{location['region']}",
                              description=location['country'],
                              url=f"https://www.google.com/maps/search/?api=1&query="
                                  f"{await urlify(location['name'])}%2C"
                                  f"{await urlify(location['region'])}%2C"
                                  f"{await urlify(location['country'])}",
                              timestamp=datetime.now(timezone.utc),
                              color=await self.determine_color(ctx, report_current)
                              )
        timestring = datetime.fromtimestamp(current['last_updated_epoch']).strftime("%I:%M %p")
        embed.set_footer(text=f"Data as of {timestring}")
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
                                  f"*Likely to Rain:* {'Yes' if forecast_today['daily_will_it_rain'] == 1 else 'No'}",
                            inline=True)
        elif snow_chance > 0 and rain_chance > 0:
            embed.add_field(name='Precipitation',
                            value=f"*Chance of Rain:* {rain_chance}%\n"
                                  f"*Likely to Rain:* {'Yes' if forecast_today['daily_will_it_rain'] == 1 else 'No'}"
                                  f"*Chance of Snow:* {snow_chance}%\n"
                                  f"*Likely to Snow:* {'Yes' if forecast_today['daily_will_it_snow'] == 1 else 'No'}",
                            inline=True)
        else:
            embed.add_field(name='Precipitation',
                            value=f"*Chance of Snow:* {snow_chance}%\n"
                                  f"*Likely to Snow:* {'Yes' if forecast_today['daily_will_it_snow'] == 1 else 'No'}",
                            inline=True)
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Weather(bot))
