import time
import psutil
import pyudev
import notify2

# Bildirim servisini başlat
notify2.init("USB/SD Depolama Bildirici")

def format_bytes(bytes_num):
    """Bayt değerini GB cinsine dönüştürür."""
    return round(bytes_num / (1024 ** 3), 2)

def handle_mount(device_path):
    """Cihaz bağlandığında (mount edildiğinde) alan bilgilerini alıp bildirim gönderir."""
    # İşletim sisteminin cihazı otomatik mount etmesi için kısa bir bekleme süresi
    time.sleep(2)
    
    # Mount edilmiş tüm disk alanlarını kontrol et
    partitions = psutil.disk_partitions(all=False)
    
    for partition in partitions:
        # Cihaz yolunun veya disk adının eşleşip eşleşmediğini doğrula
        if device_path in partition.device or partition.device in device_path:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                total_gb = format_bytes(usage.total)
                percent_used = usage.percent
                fstype = partition.fstype.upper() if partition.fstype else "Bilinmiyor"
                mount_point = partition.mountpoint
                
                # Bildirim başlığı ve içeriği
                title = "💾 Yeni Depolama Cihazı Takıldı"
                message = (
                    f"<b>Bağlantı Noktası:</b> {mount_point}\n"
                    f"<b>Dosya Biçimi:</b> {fstype}\n"
                    f"<b>Toplam Kapasite:</b> {total_gb} GB\n"
                    f"<b>Doluluk Oranı:</b> %{percent_used}"
                )
                
                # Bildirimi oluştur ve göster
                n = notify2.Notification(title, message, "drive-removable-media")
                n.set_urgency(notify2.URGENCY_NORMAL)
                n.show()
                return
            except PermissionError:
                continue

def main():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    # Yalnızca blok cihazlardaki 'add' (ekleme) olaylarını dinle
    monitor.filter_by(subsystem='block', device_type='partition')
    
    print("USB ve SD Kart takılma olayları dinleniyor... (Durdurmak için Ctrl+C)")
    
    for device in iter(monitor.poll, None):
        if device.action == 'add':
            device_node = device.device_node
            if device_node:
                handle_mount(device_node)

if __name__ == '__main__':
    main()
