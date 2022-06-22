import downloader
import sys
import threading
#a = downloader.Download("https://speed.hetzner.de/1GB.bin", "1GB.bin")



#a = downloader.Download("https://cdimage.kali.org/kali-2022.1/kali-linux-2022.1-installer-arm64.iso", "kali-linux-2022.1-installer-arm64.iso")
#print(a.ranges)


b = downloader.Download(sys.argv[1], sys.argv[2])
#c = downloader.Download("https://cdimage.kali.org/kali-2022.1/kali-linux-2022.1-installer-arm64.iso", "Kali.iso")
t1 = threading.Thread(target=b.start)
#t2 = threading.Thread(target=c.start)
t1.start()
#t2.start()
t1.join()
#t2.join()