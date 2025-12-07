import numbers
import RPi.GPIO as GPIO
from displayhatmini import DisplayHATMini as Display
from PIL import Image, ImageDraw, ImageFont
import time

import qrcode
from helper import *


class DisplayMenu:
    def __init__(self, menu_items, title, backlight=1.0, font=ImageFont.load_default(18)):

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
        self.draw.text((20, 20), self.title, font=ImageFont.load_default(24), fill=(255, 255, 255))
        y = 60
        for i, item in enumerate(self.menu_items):
            if i == self.selected:
                color = (0, 255, 0) 
            else: 
                color = (180, 180, 180)

            if item == "Exit":
                color = (255, 0, 0)
                y += 25
            prefix = "> " if i == self.selected else "  "
            self.draw.text((30, y), prefix + item, font=self.font, fill=color, align="center")
            y += 25
        self.display.display()

    def show_loader(self, msg, margin_left = 40, margin_top = 100):
        self.draw.rectangle((0, 0, 320, 240), (0, 0, 0))
        self.draw.text((margin_left, margin_top), msg, font=self.font, fill=(255, 255, 255))

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
            self.draw.rectangle((145, 135, 150, 140), (s1, s1, s1))
            self.draw.rectangle((155, 135, 160, 140), (s2, s2, s2))
            self.draw.rectangle((165, 135, 170, 140), (s3, s3, s3))
            # loader square row #2
            self.draw.rectangle((145, 145, 150, 150), (s4, s4, s4))
            self.draw.rectangle((155, 145, 160, 150), (s5, s5, s5))
            self.draw.rectangle((165, 145, 170, 150), (s6, s6, s6))
            # loader square row #3
            self.draw.rectangle((145, 155, 150, 160), (s7, s7, s7))
            self.draw.rectangle((155, 155, 160, 160), (s8, s8, s8))
            self.draw.rectangle((165, 155, 170, 160), (s9, s9, s9))

            self.display.display()
            time.sleep(0.125)

    def show_qr(self, img, msg = "Scan QR code"):
        self.draw.rectangle((0, 0, 320, 240), (0, 0, 0))
        self.img.paste(img.resize((170, 170)), (75, 60))
        self.draw.text((20, 20), msg, font=ImageFont.load_default(16), fill=(255, 255, 255))
        self.display.display()

    def show_message(self, msg, margin_left=40, margin_top=100):
        self.draw.rectangle((0, 0, 320, 240), (0, 0, 0))
        self.draw.text((margin_left, margin_top), msg, font=self.font, fill=(255, 255, 255))
        self.display.display()

    def param_menu(self, params: dict, title="Parameters"):
        # TODO: Make interactive, this is just a placeholder to show params
        # This would be input via buttons to toggle options
        self.draw.rectangle((0, 0, 320, 240), (0, 0, 0))  # clear screen
        self.draw.text((20, 20), title, font=ImageFont.load_default(24), fill=(255, 255, 255))
        self.draw.text((20, 50), "(Press X to start)", font=self.font, fill=(180, 180, 180))
        y = 80
        for key, value in params.items():
            color = (39, 245, 245)
            line = f"{key}: {value}"
            self.draw.text((20, y), line, font=ImageFont.load_default(16), fill=color, align="center")
            y += 25

        self.draw.text((20, y+25), "<Back", font=self.font, fill=(180, 180, 180))
        self.display.display()

    def set_backlight(self, brightness):
        self.display.set_backlight(brightness)


# --- Select workspace ---

def workspace_menu():
    workspace_menu = DisplayMenu(title="Choose workspace", menu_items=get_workspaces())
    selected_id = workspace_menu.menu_items[workspace_menu.selected]
    workspace_menu.render_menu()

    while True:
        if not GPIO.input(workspace_menu.BUTTON_B):
            workspace_menu.selected = (workspace_menu.selected + 1) % len(workspace_menu.menu_items)
            workspace_menu.render_menu()
        if not GPIO.input(workspace_menu.BUTTON_A):
            workspace_menu.selected = (workspace_menu.selected - 1) % len(workspace_menu.menu_items)
            workspace_menu.render_menu()
        if not GPIO.input(workspace_menu.BUTTON_X):
            selected_id = workspace_menu.menu_items[workspace_menu.selected]
            return selected_id
        time.sleep(0.05)
    
id = workspace_menu()


device_menu = DisplayMenu(title=id, menu_items=["Trim reads", "Quality control", "Assembly", "Mappings", "History", "Exit"])
device_menu.render_menu()

# wait for fastp to finish, then generate QR once
loader = device_menu.show_loader

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
            if choice == "History":
                history = get_workspace_history(id)
                device_menu.draw.rectangle((0, 0, 320, 240), (0, 0, 0))  # clear screen
         

                y = 20
                device_menu.draw.text((20, y), "Command | Params | Time", font=ImageFont.load_default(24), fill=(255, 255, 255))
                y += 8
                for cmd in history:
                    cmd_type = cmd.get("type")
                    params = cmd.get("params")
                    dt = cmd.get("created_at")
                    y += 25
                    device_menu.draw.text((20, y), f"{cmd_type} | {params} | {dt}", font=ImageFont.load_default(18), fill=(255, 255, 255))
                device_menu.display.display()
            if choice == "Trim reads":

                while True:
                    device_menu.param_menu({
                        "cut_right": True, 
                        "detect_adapter_for_pe": True, 
                        "overrepresentation_analysis": True, 
                        "correction": True
                    }, title="fastp options")
                    time.sleep(0.2)
                    if not GPIO.input(device_menu.BUTTON_X):
                        break

                task_id = fastp(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

                wait_for_task(task_id, interval=0, verbose=True, callback=loader, args=("Trimming reads...", 96, 102))
                report_url = fastp_report(id)
                img = qrcode.make(report_url)
                device_menu.show_qr(img, msg=f"See the fastp report in your browser:")
                while True:
                    if not GPIO.input(device_menu.BUTTON_X):
                        device_menu.render_menu()
                        time.sleep(0.2)
                        break
                    time.sleep(0.2)
            if choice == "Quality control":

                while True:
                    device_menu.param_menu({
                        "min_length": "DEFAULT", 
                        "contaminants": "NONE", 
                        "adapters": "NONE", 
                        "kmers": 7
                    }, title="fastqc options")
                    time.sleep(0.2)
                    if not GPIO.input(device_menu.BUTTON_X):
                        break

                task_id = fastqc(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

                wait_for_task(task_id, interval=0, verbose=True, callback=loader, args=("Running quality control...", 68, 102))


                # show just R1 report as example
                report_url = fastqc_report(id, filename='trimmed_anc_R1')
                # wait for fastqc to finish, then generate QR once

                img = qrcode.make(report_url)
                device_menu.show_qr(img, msg=f"See the fastqc report in your browser:")
                while True:
                    if not GPIO.input(device_menu.BUTTON_X):
                        device_menu.render_menu()
                        time.sleep(0.2)
                        break
                    time.sleep(0.2)
            if choice == "Assembly":

                while True:
                    device_menu.param_menu({
                        "plasmid": False, 
                        "bio": False, 
                        "rna": False, 
                        "rnaviral": False,
                        "corona": False,
                        "iontorrent": False,
                        "nanopore": False,
                    }, title="spades options")
                    time.sleep(0.2)
                    if not GPIO.input(device_menu.BUTTON_X):
                        break

                task_id = assemble(['anc_R1.fastq.gz', 'anc_R2.fastq.gz'], id)

                # wait for assembly/fastqc to finish
                wait_for_task(task_id, interval=0, verbose=True, callback=loader, args=("Assembling reads...", 87, 102))
                
                device_menu.show_message("Mapping Complete!", 90, 102)
                time.sleep(2)

                device_menu.render_menu()
                
            if choice == "Mappings":

                while True:
                    device_menu.param_menu({
                        "index_file": f'/workspace/{id}/...', 
                        "BAM target": "anc"
                    }, title="BWA")
                    time.sleep(0.2)
                    if not GPIO.input(device_menu.BUTTON_X):
                        break

                task_id = bwa_index([f'/workspace/{id}/assembly/scaffolds.fasta'], id)
                wait_for_task(task_id, interval=0, verbose=True, callback=loader, args=("Indexing files...", 102, 102))
                
                task_id = bwa_mem([f'/workspace/{id}/assembly/scaffolds.fasta', f'/workspace/{id}/trimmed/trimmed_anc_R1.fastq.gz', f'/workspace/{id}/trimmed/trimmed_anc_R2.fastq.gz'], id, out='anc.sam')
                wait_for_task(task_id, interval=0, verbose=True, callback=loader, args=("Running alignment...", 88, 102))
                
                task_id = samtools_convert('anc', 'anc', id)
                wait_for_task(task_id, interval=0, verbose=True, callback=loader, args=("Converting BAM files...", 88, 102))
           
                device_menu.show_message("Mapping Complete!", 88, 102)
                time.sleep(2)

                igv_url = gen_igv_url(id)
                img = qrcode.make(igv_url)
                device_menu.show_qr(img, msg=f"View genome in IGV browser:")

                while True:
                    if not GPIO.input(device_menu.BUTTON_X):
                        device_menu.render_menu()
                        time.sleep(0.05)
                        break
                    time.sleep(0.05)

            if choice == "Exit":
                break
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
    device_menu.display.set_backlight(0)
