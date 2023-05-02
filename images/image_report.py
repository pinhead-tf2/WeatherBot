import time

from datetime import datetime, timezone
from catppuccin import Flavour
from PIL import Image, ImageDraw, ImageFont

# colors
mocha = Flavour.mocha()
rosewater = mocha.rosewater.rgba
flamingo = mocha.flamingo.rgba
pink = mocha.pink.rgba
maroon = mocha.maroon.rgba
yellow = mocha.yellow.rgba
green = mocha.green.rgba
sky = mocha.sky.rgba
blue = mocha.blue.rgba

# greys
text = mocha.text.rgba
subtext0 = mocha.subtext0.rgba
overlay2 = mocha.overlay2.rgba
overlay1 = mocha.overlay1.rgba
overlay0 = mocha.overlay0.rgba
surface0 = mocha.surface0.rgba
base = Flavour.frappe().base.rgba  # looks nicer for the bg
crust = mocha.crust.rgba

# font choice and size
fontChoice = "Mako-Regular.ttf"
headerSize1 = ImageFont.truetype(fontChoice, 48)
headerText2 = ImageFont.truetype(fontChoice, 32)
normalText = ImageFont.truetype(fontChoice, 20)
footerText1 = ImageFont.truetype(fontChoice, 16)
footerText2 = ImageFont.truetype(fontChoice, 14)

# padding
preferredPadding = 6
preferredImagePadding = 64
preferredConditionPadding = 64

# strftime display
strftimeString = '%I:%M %p (%Z)'


def determine_length(report):
    location = report['location']
    canvas = Image.new(mode="RGBA", size=(1, 1), color=base)
    imgDraw = ImageDraw.Draw(canvas)
    imageSize = 500
    availableSpace = (500 - 64 - preferredPadding)

    # get the 3 longest things
    # get length of name and region, combined with a comma and space
    size = imgDraw.textlength(f"{location['name']}, "f"{location['region']}", headerSize1)
    # size = imgDraw.textbbox((preferredPadding, 0), f"{location['name']}, "f"{location['region']}", headerSize1)
    # if it's larger than the default size accounting for the icon and padding (available space)
    if size > availableSpace:
        newSize = int(size) - 140  # fixes weird padding issue
        if newSize - 140 > availableSpace:  # checks to ensure there won't be overlap issues
            imageSize = newSize
        else:  # fallback for if there is overlap issues
            imageSize = size

    # find ideal padding for countryLength and weatherConditionLength
    countryLength = imgDraw.textlength(location['country'], normalText)
    weatherConditionLength = imgDraw.textlength(report['current']['condition']['text'], normalText)
    # it's weird, but it works
    # determines how much overlap there is by subtracting the country's total consumed space
    # 360 - 221 = 139 (bad, goes to if condition)
    # 122 - 221 = -99 (good)
    overusedSpace = (weatherConditionLength + preferredPadding) - (countryLength + preferredPadding)
    if overusedSpace > 0 and overusedSpace > imageSize:  # if it's larger than previous, then replace
        imageSize = 500 + overusedSpace
    return int(imageSize)


def determine_outlook(code):
    outlook = "Clear"
    colorChoice = text

    match code:
        # overcast, fog
        case 1009 | 1135:
            outlook = "Cloudy"
            colorChoice = overlay2

        # patchy light drizzle, light drizzle, patchy light rain, light rain,light rain shower, moderate rain at times,
        # moderate rain
        case 1150 | 1153 | 1180 | 1183 | 1240 | 1186 | 1189:
            outlook = "Rainy"
            colorChoice = green

        # patchy light rain with thunder, patchy light rain with thunder, thundery outbreaks possible,
        # heavy rain at times, heavy rain, torrential rain shower, moderate or heavy rain with thunder
        case 1273 | 1087 | 1192 | 1195 | 1246 | 1276:
            outlook = "Stormy"
            colorChoice = green

        # patchy light snow, light snow, light snow showers, light showers of ice pellets,
        # patchy light snow with thunder, blowing snow, patchy moderate snow, moderate snow, ice pellets
        case 1210 | 1213 | 1255 | 1261 | 1279 | 1114 | 1216 | 1219 | 1237:
            outlook = "Snowy"
            colorChoice = sky

        # patchy heavy snow, heavy snow, moderate or heavy snow showers, moderate or heavy showers of ice pellets,
        # moderate or heavy snow with thunder, blizzard, freezing fog
        case 1222 | 1225 | 1258 | 1264 | 1282 | 1117 | 1147:
            outlook = "Blizzard-Filled"
            colorChoice = blue

        # patchy sleet possible, light sleet, light sleet showers, moderate or heavy sleet
        case 1069 | 1204 | 1249 | 1207:
            outlook = "Sleet-Filled"
            colorChoice = flamingo

        # patchy freezing drizzle possible, light freezing rain, freezing drizzle, heavy freezing drizzle,
        # moderate or heavy freezing rain
        case 1072 | 1198 | 1168 | 1171 | 1201:
            outlook = "Freezing Rain-Filled"
            colorChoice = pink

    return outlook, colorChoice


def precipitation_string(current, forecast):
    precipChance = 0
    precipType = "rain"
    dayStage = 'Day' if current['is_day'] else 'Night'

    rain_chance = forecast['daily_chance_of_rain']
    snow_chance = forecast['daily_chance_of_snow']

    if rain_chance > snow_chance:
        precipChance = rain_chance
    elif snow_chance > rain_chance:
        precipChance = snow_chance
        precipType = "snow"
    elif rain_chance == 0 and snow_chance == 0:
        precipType = "rain" if current['temp_f'] > 35.0 else "snow"

    dayOutlook, dayColor = determine_outlook(forecast['condition']['code'])

    # return precip chance, type of precip, overall outlook and current time
    return precipChance, precipType, f"{dayOutlook} {dayStage}", dayColor


def generate_image(report):
    startTime = time.time()
    # setup for repetition reduction
    location = report['location']
    current = report['current']
    condition = current['condition']
    forecast = report['forecast']['forecastday'][0]['day']
    alerts = report['alerts']
    isDay = True if current['is_day'] == 1 else False
    precipChance, precipType, dayOutlook, dayColor = precipitation_string(current, forecast)

    # colors
    footerColor = crust if isDay else text

    # background
    # should scale based on location name's length, minimum of 500px
    imageSize = determine_length(report)
    rightAlignment = imageSize - preferredPadding
    canvas = Image.new(mode="RGBA", size=(imageSize, 200), color=base)
    # weather icon
    # use the given image code to load assets, but do an isday check first, use ternary
    icon = Image.open(f"assets/{condition['icon'][35:]}", 'r')

    imgDraw = ImageDraw.Draw(canvas)  # setup drawer
    imgDraw.font = normalText  # default font
    imgDraw.fontmode = "L"  # antialiases text

    # footer
    # draw the footer's bar
    imgDraw.rectangle((0, 176, imageSize, 200), fill=rosewater if isDay else overlay0)
    # takes the data's epoch time, makes it aware (timezone issues), and converts it to the preferred display string
    dataRequestTime = datetime.fromtimestamp(current['last_updated_epoch'], timezone.utc).strftime(strftimeString)
    imgDraw.text((preferredPadding, 179), f"Data as of {dataRequestTime} - WeatherAPI.com",
                 font=footerText2,
                 fill=footerColor)  # data time footer2
    # takes the user's request time in utc, and convets it to preferred display string
    imgDraw.text((rightAlignment, 179), f"Requested at "
                                        f"{datetime.now(timezone.utc).strftime(strftimeString)}",
                 font=footerText2,
                 fill=footerColor,
                 anchor="ra")  # request time footer2

    # left side
    imgDraw.text((preferredPadding, 0), f"{location['name']}, "f"{location['region']}",
                 font=headerText2,
                 fill=text)  # city, region header2
    imgDraw.text((preferredPadding, 39), location['country'], fill=text)  # country normal
    # current temperature header1
    imgDraw.text((preferredPadding, 52), f"{current['temp_f']}°", font=headerSize1, fill=text)
    offset = imgDraw.textlength(f"{current['temp_f']}°", headerSize1) - 5  # get X anchor via the length of the font
    # feels like normal
    imgDraw.text((preferredPadding + offset, 86), f"{current['feelslike_f']}°", font=footerText1, fill=text)
    imgDraw.text((preferredPadding, 105), f"{current['humidity']}% humidity", fill=text)  # humidity normal
    alertCount = len(alerts['alert'])
    imgDraw.text((preferredPadding, 150), f"{alertCount} Alerts",
                 font=footerText1,
                 fill=overlay2 if alertCount == 0 else maroon)  # alert footer1

    # right side
    # pastes weather icon
    canvas.paste(icon, (rightAlignment - 64, 0), icon)
    # current condition normal
    imgDraw.text((rightAlignment, 55), f"{condition['text']}", fill=text, align="right", anchor="ra")
    # high/low temp normal
    imgDraw.text((rightAlignment, 81), f"{forecast['maxtemp_f']}°/{forecast['mintemp_f']}°",
                 fill=text,
                 align="right",
                 anchor="ra")
    # precip chance normal
    imgDraw.text((rightAlignment, 107), f"{precipChance}% chance of {precipType}",
                 fill=text,
                 align="right",
                 anchor="ra")
    imgDraw.text((rightAlignment, 150), f"{dayOutlook}",
                 font=footerText1,
                 fill=dayColor,
                 align="right",
                 anchor="ra")  # day conditions footer1

    # print(f"image finished processing | time to process: {round(time.time() - startTime, 5)} seconds")
    return canvas
