**KHADAS SETUP FOR POWER RELATIONS**

**Fresh Install Procedure (Khadas):**
1.  Insert the MicroSD card with the Krescue image burned onto it
2.  Reset Khadas Vim3 into Krescue environment by quickly pressing the middle button on the side 3 times
3.  Once booted into Krescue environment, then format EMMC memory
4.  Burn Ubuntu 4.9 EMMC to the Khadas Vim3

**Khadas Initial Boot Setup:**
1.  Username and password are both “khadas” (no quotes)
2.  Open terminal and update the system with apt-get update and apt-get upgrade, or sudo apt update && sudo apt upgrade -y
3.  Install Pip by typing:
```    
sudo apt install python3-pip
```
4.  Install Rpi.GPIO library by git cloning the library for Khadas (https://github.com/frank180/RPi.GPIO-Khadas)
5.  Type:
```
git clone https://github.com/frank180/RPi.GPIO-Khadas.git
```
6.  Navigate to the directory where the files were cloned (likely Desktop/Rpi.GPIO-Khadas)
7.  Type:
```
sudo python setup.py build install
sudo python3 setup.py build install
```
8.  If this has correctly installed the library then type:
```
sudo apt-get install python-rpi.gpio
sudo apt-get install python3-rpi.gpio
```
9.  Install the Beautiful Soup library by typing:
```
sudo apt-get install python3-bs4
```
10. Set the Script to Run
11. On the command line or in the terminal type sudo nano /home/khadas/.bashrc
12. Scroll to the bottom of the file and type:
```
python3 /home/khadas/script.py --p /home/khadas --t 350
```
13. Press Ctrl-X to exit
14. Press 'Y' to save changes and then press enter
15. Type sudo reboot

**Setup Autologin:**
1. On the command line or in the terminal type:
```
sudo systemctl edit getty@tty1.service
```
2. A blank file will popup, type the following:
```
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin khadas %I $TERM
Type=idle
```
3. Press Ctrl-X to exit
4. Press ‘Y’ to save changes and then press enter

**Set Ubuntu to Start in Command Line:**
1. To boot to command-line, type:
```
sudo systemctl set-default multi-user.target
sudo reboot
```
2. To boot to GUI environment, type:
```
sudo systemctl set-default graphical.target
sudo reboot
```
**Change Font in Command Line:**
1. Change Font in the command line, type:
```
sudo dpkg-reconfigure console-setup
```
(font used is Terminus at least 10x20 to get the sharp look)
