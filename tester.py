import downloader
import sys
import threading
#a = downloader.Download("https://speed.hetzner.de/1GB.bin", "1GB.bin")



#a = downloader.Download("https://cdimage.kali.org/kali-2022.1/kali-linux-2022.1-installer-arm64.iso", "kali-linux-2022.1-installer-arm64.iso")
#print(a.ranges)

c = downloader.Download("http://archive.ubuntu.com/ubuntu/dists/bionic/main/installer-amd64/current/images/netboot/mini.iso", "mini.iso")
a = downloader.Download("https://speed.hetzner.de/1GB.bin", "1_1GB.bin")
t2 = threading.Thread(target=a.start)
t3 = threading.Thread(target=c.start)
t2.start()
t3.start()
t2.join()
t3.join()
#b.start()
