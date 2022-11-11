# poweroutage-api

**poweroutage.us key**</br>
Access to live outage data provided through poweroutage.us via REST API.

**Updating the code remotely**
1. Update and upgrade:
```
sudo apt-get update
sudo apt-get upgrade
```
2. Determine the filename of the Python script on Vim3 at Rib:
```
ls
```
*Note: likely named something like “power-relations-california.py”

3. Transferring existing Python script at Rib:

Upload file using transfer.sh:
```
curl --upload-file my-file.txt https://transfer.sh/myfile.txt
```
Returns a unique link, such as:
```
https://transfer.sh/Kvz4Xk/my-file.txt
```
To download the file:
```
curl https://transfer.sh/Kvz4Xk/my-file.txt -o my-file.txt
```
*Note: downloaded file is sent to Users/mathewkneebone/*

4. Double-check the the file to compare it with api version (e.g. GPIO usage)

5. Git clone the repository onto the Vim3 at Rib
```
git clone https://github.com/mathew-kneebone/power-relations.git
```
*Note: repository must first be set to public, also ensure the authkey.txt is included*

6. Move the “vim-power-auth-california.py” and “authkey.txt” files to user directory:
```
mv power-relations/poweroutage-api/vim-power-auth-california.py /home/khadas/
mv power-relations/poweroutage-api/authkey.txt /home/khadas/
```
7. Update file name in .bashrc:
```
sudo nano /home/khadas/.bashrc
```
8. Scroll to the bottom and change filename:
```
python3 /home/khadas/vim-power-auth-california.py --p /home/khadas --t 350
```
9. Save and exit out of nano:
```
ctrl + x
y
Enter
```
10. Reboot system:
```
sudo reboot
```
