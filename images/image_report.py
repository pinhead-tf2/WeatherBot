import time
from PIL import Image, ImageDraw, ImageFont

startTime = time.time()

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

# background
# should scale based on location name's length, minimum of 500px
canvas = Image.new(mode="RGBA", size=(500, 200), color=baseColor)
# weather icon
# substring the given url in icon for the image
icon = Image.open('../assets/day/389.png', 'r')

imgDraw = ImageDraw.Draw(canvas)  # setup drawer
imgDraw.fill = True
imgDraw.font = makoNormal
imgDraw.fontmode = "L"

# Left Side Content
imgDraw.rectangle((0, 176, 500, 200), fill=overlay2Color)  # replace the 500 and the fill
imgDraw.text((6, 0), "Minneapolis, Minnesota", font=makoHeader2, fill=textColor)  # city, region header2
imgDraw.text((6, 39), "United States of America", fill=textColor)  # country normal
imgDraw.text((6, 52), "44.1°", font=makoHeader1, fill=textColor)  # current temperature header1
# get X anchor via the length of the font
# feels like normal
imgDraw.text((6 + imgDraw.textlength("44.1°", makoHeader1) - 5, 86), "36.6°", font=makoFooter1, fill=textColor)
imgDraw.text((6, 105), "95% humidity", fill=textColor)  # humidity normal
imgDraw.text((6, 150), "3 Alerts", font=makoFooter1, fill=redColor)  # alert footer1

# Right Side Content
canvas.paste(icon, (430, 0), icon)

print(f"image finished processing | Time to process: {round(time.time() - startTime, 5)} seconds")

canvas.show()  # preview
