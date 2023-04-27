import time
from PIL import Image, ImageDraw, ImageFont

flamingoColor = (242, 205, 205)
pinkColor = (245, 194, 231)
redColor = (235, 160, 172)
orangeColor = (250, 179, 135)
yellowColor = (249, 226, 175)
greenColor = (166, 227, 161)
blueColor = (116, 199, 236)
textColor = (205, 215, 244)
overlay2Color = (147, 153, 178)
baseColor = (48, 52, 70)
crustColor = (24, 25, 38)

makoHeader1 = ImageFont.truetype("Mako-Regular.ttf", 48)
makoHeader2 = ImageFont.truetype("Mako-Regular.ttf", 32)
makoNormal = ImageFont.truetype("Mako-Regular.ttf", 20)
makoFooter1 = ImageFont.truetype("Mako-Regular.ttf", 16)
makoFooter2 = ImageFont.truetype("Mako-Regular.ttf", 14)

preferredPadding = 6
preferredImagePadding = 64
preferredConditionPadding = 96


def determine_length(report):
    location = report['location']
    canvas = Image.new(mode="RGBA", size=(1, 1), color=baseColor)
    imgDraw = ImageDraw.Draw(canvas)
    padding = 0

    # get the 3 longest things
    nameRegionLength = imgDraw.textlength(f"{location['name']}, "f"{location['region']}", makoHeader1)
    # 64px padding is best between image and nameRegionLength
    runoff = (nameRegionLength + preferredPadding) - (500 - 64 - preferredPadding)
    if runoff > 0:
        padding = runoff + preferredImagePadding

    # find ideal padding for countryLength and weatherConditionLength
    # try 80px?
    countryLength = imgDraw.textlength(location['country'])
    weatherConditionLength = imgDraw.textlength(report['current']['condition']['text'])
    # 360 - 221 = 139 (bad)
    # 122 - 221 = -99 (good)
    overusedSpace = (weatherConditionLength + preferredPadding) - (countryLength + preferredPadding)
    if overusedSpace > 0 and overusedSpace > padding:
        padding = overusedSpace + preferredConditionPadding

    return padding


def generate_image(report):
    # background
    # should scale based on location name's length, minimum of 500px
    padding = determine_length(report)
    canvas = Image.new(mode="RGBA", size=(500+padding, 200), color=baseColor)
    imgDraw = ImageDraw.Draw(canvas)  # setup drawer
    return canvas


def test_image():
    # background
    # should scale based on location name's length, minimum of 500px
    canvas = Image.new(mode="RGBA", size=(500, 200), color=baseColor)
    # weather icon
    # use the given image code to load assets, but do an isday check first, use ternary
    icon = Image.open('../assets/day/122.png', 'r')

    imgDraw = ImageDraw.Draw(canvas)  # setup drawer
    imgDraw.font = makoNormal  # default font
    imgDraw.fontmode = "L"  # antialiases text

    # Left Side Content
    imgDraw.rectangle((0, 176, 500, 200), fill=overlay2Color)  # replace the 500 and the fill
    imgDraw.text((6, 0), "Minneapolis, Minnesota", font=makoHeader2, fill=textColor)  # city, region header2
    imgDraw.text((6, 39), "United States of America", fill=textColor)  # country normal
    imgDraw.text((6, 52), "44.1°", font=makoHeader1, fill=textColor)  # current temperature header1
    offset = imgDraw.textlength("44.1°", makoHeader1) - 5  # get X anchor via the length of the font
    imgDraw.text((6 + offset, 86), "36.6°", font=makoFooter1, fill=textColor)  # feels like normal
    imgDraw.text((6, 105), "95% humidity", fill=textColor)  # humidity normal
    imgDraw.text((6, 150), "3 Alerts", font=makoFooter1, fill=redColor)  # alert footer1
    imgDraw.text((6, 179), "Data as of 2:15 PM - WeatherAPI.com", font=makoFooter2,
                 fill=crustColor)  # data time footer2

    # Right Side Content
    canvas.paste(icon, (430, 0), icon)
    imgDraw.text((496, 55), "Overcast", fill=textColor, align="right", anchor="ra")  # current condition normal
    imgDraw.text((496, 81), "48.2°/31.8°", fill=textColor, align="right", anchor="ra")  # high/low temp normal
    imgDraw.text((496, 107), "87% chance of rain", fill=textColor, align="right", anchor="ra")  # precip chance normal
    imgDraw.text((496, 150), "Stormy Day", font=makoFooter1, fill=yellowColor, align="right",
                 anchor="ra")  # day conditions footer1
    imgDraw.text((496, 179), f"Requested at 2:22 PM | Generation Time: {round(time.time() - startTime, 5)}", font=makoFooter2, fill=crustColor,
                 anchor="ra")  # request time footer2

    print(f"image finished processing | Time to process: {round(time.time() - startTime, 5)} seconds")
    canvas.show()  # preview


if __name__ == '__main__':
    startTime = time.time()
    file = open("../text.json", "r")
    generate_image(file.read())
    file.close()
