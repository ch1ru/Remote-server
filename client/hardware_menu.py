import RPi.GPIO as GPIO
from displayhatmini import DisplayHATMini as Display
from PIL import Image, ImageDraw, ImageFont
import time

import qrcode
from helper import *


class DisplayMenu:
    def __init__(self, menu_items, title, backlight=1.0, font=ImageFont.load_default()):

        self.img = Image.new("RGB", (320, 240), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.img)
        self.display = Display(self.img)

        self.backlight = backlight  # default full brightness

        # --- GPIO pins for Display HAT Mini buttons ---
        self.BUTTON_A = 5
        self.BUTTON_B = 6
        self.BUTTON_X = 16
        self.BUTTON_Y = 24

        self.font = font
        self.menu_items = menu_items
        self.title = title
        self.selected = 0

        self.setup_gpio()

    # --- Setup GPIO ---
    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        for pin in [self.BUTTON_A, self.BUTTON_B, self.BUTTON_X, self.BUTTON_Y]:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def render_menu(self):
        self.draw.rectangle((0, 0, 320, 240), (0, 0, 0))  # clear screen
        self.draw.text((20, 20), self.title, font=self.font, fill=(0, 0, 255))
        y = 50
        for i, item in enumerate(self.menu_items):
            color = (0, 255, 0) if i == self.selected else (180, 180, 180)
            prefix = "> " if i == self.selected else "  "
            self.draw.text((30, y), prefix + item, font=self.font, fill=color)
            y += 30
        self.display.display()

    def show_loader(self, msg):
        self.draw.rectangle((0, 0, 320, 240), (0, 0, 0))
        self.draw.text((40, 100), msg, font=self.font, fill=(255, 255, 255))

        for i in range(8):

            s1 = 0 if i == 0 else 255
            s2 = 0 if i == 1 else 255
            s3 = 0 if i == 2 else 255
            s6 = 0 if i == 3 else 255
            s9 = 0 if i == 4 else 255
            s8 = 0 if i == 5 else 255          
            s7 = 0 if i == 6 else 255
            s4 = 0 if i == 7 else 255
            s5 = 255

            # loader square row #1
            self.draw.rectangle((135, 140, 145, 150), (s1, s1, s1))
            self.draw.rectangle((155, 140, 165, 150), (s2, s2, s2))
            self.draw.rectangle((175, 140, 185, 150), (s3, s3, s3))
            # loader square row #2
            self.draw.rectangle((135, 160, 145, 170), (s4, s4, s4))
            self.draw.rectangle((155, 160, 165, 170), (s5, s5, s5))
            self.draw.rectangle((175, 160, 185, 170), (s6, s6, s6))
            # loader square row #3
            self.draw.rectangle((135, 180, 145, 190), (s7, s7, s7))
            self.draw.rectangle((155, 180, 165, 190), (s8, s8, s8))
            self.draw.rectangle((175, 180, 185, 190), (s9, s9, s9))

            self.display.display()
            time.sleep(0.1)

    def show_qr(self, img):
        self.img.paste(img.resize((200, 200)), (60, 20))
        self.display.display()

    def show_message(self, msg):
        self.draw.rectangle((0, 0, 320, 240), (0, 0, 0))
        self.draw.text((40, 100), msg, font=self.font, fill=(255, 255, 255))

    def set_backlight(self, brightness):
        self.display.set_backlight(brightness)


id = "test_yyy"
device_menu = DisplayMenu(title=id, menu_items=["Trim reads", "Quality control", "Assembly", "Mappings", "IGV Viewer", "Exit"])
device_menu.render_menu()

# --- Main loop ---
try:
    while True:
        if not GPIO.input(device_menu.BUTTON_B):  # Down
            device_menu.selected = (device_menu.selected + 1) % len(device_menu.menu_items)
            device_menu.render_menu()
        if not GPIO.input(device_menu.BUTTON_A):  # Up
            device_menu.selected = (device_menu.selected - 1) % len(device_menu.menu_items)
            device_menu.render_menu()
        if not GPIO.input(device_menu.BUTTON_X):  # Select
            choice = device_menu.menu_items[device_menu.selected]
            if choice == "Trim reads":

                # wait for fastp to finish, then generate QR once
                loader = device_menu.show_loader

                task_id = fastp(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

                
                wait_for_task(task_id, interval=0.5, verbose=True, callback=loader, args=("Trimming reads...",))
                report_url = fastp_report(id)
                img = qrcode.make(report_url)
                device_menu.show_qr(img)
                while True:
                    if not GPIO.input(device_menu.BUTTON_X):
                        device_menu.render_menu()
                        time.sleep(0.2)
                        break
                    time.sleep(0.2)
            if choice == "Quality control":
                task_id = fastqc(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

                # wait for fastqc to finish, then generate QR once
                wait_for_task(task_id, interval=1, verbose=True)
                # show just R1 report as example
                report_url = fastqc_report(id, filename='trimmed_anc_R1')
                img = qrcode.make(report_url)
                device_menu.show_qr(img)
                while True:
                    if not GPIO.input(device_menu.BUTTON_X):
                        device_menu.render_menu()
                        break
                    time.sleep(0.2)
            if choice == "Assembly":
                task_id = assemble(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

                # wait for assembly/fastqc to finish
                wait_for_task(task_id, interval=1, verbose=True)
                
                device_menu.show_message("Assembly Complete!")
            if choice == "Mappings":
                bwa_index([f'/workspace/{id}/assembly/scaffolds.fasta'], id)
                bwa_mem([f'/workspace/{id}/assembly/scaffolds.fasta', f'/workspace/{id}/trimmed/trimmed_anc_R1.fastq.gz', f'/workspace/{id}/trimmed/trimmed_anc_R2.fastq.gz'], id, out='anc.sam')
                samtools_convert('anc', 'anc', id)
            if choice == "IGV Viewer":
                task_id = bwa_index([f'/workspace/{id}/assembly/scaffolds.fasta'], id)

                wait_for_task(task_id, interval=1, verbose=True)

                task_id = bwa_mem([f'/workspace/{id}/assembly/scaffolds.fasta', f'/workspace/{id}/trimmed/trimmed_anc_R1.fastq.gz', f'/workspace/{id}/trimmed/trimmed_anc_R2.fastq.gz'], id, out='anc.sam')
                
                wait_for_task(task_id, interval=1, verbose=True)
                
                task_id = samtools_convert('anc', 'anc', id)

                wait_for_task(task_id, interval=1, verbose=True)

                igv_url = gen_igv_url(id)
                img = qrcode.make(igv_url)
                img.save(f'/qr/igv_{id}_qrcode.png')

                device_menu.display.img.show(img)
                device_menu.render_menu()

            if choice == "Exit":
                break
            time.sleep(0.3)
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
    device_menu.display.set_backlight(0)
