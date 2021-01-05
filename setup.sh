sudo apt-get install python-gobject bluez bluez-tools bluez-firmware python-bluez python-dev python-pip -y
sudo pip install evdev
sudo apt-get install python-dbus  -y
sudo apt-get install python-gtk2 -y
sudo apt-get install python3-bluez python3-evdev -y
sudo apt-get install git-core -y
sudo apt-get install tmux -y
sudo cp dbus/org.yaptb.btkbservice.conf /etc/dbus-1/system.d
git clone https://github.com/Eelviny/nxt-python.git ../nxt-python
cd ../nxt-python
sudo python3 setup.py install
