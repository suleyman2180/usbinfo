import os
import time
import subprocess
import psutil
import pyudev

def bytes_to_gb(bytes_value):
    """Bayt değerini GB formatına çevirir."""
    return round(bytes_value / (1024 ** 3), 2)

def send_notification(title, message, icon="drive-removable-media"):
    """Ubuntu masaüstüne bildirim gönderir."""
    try:
        # Arka planda veya systemd altında çalışırken masaüstü ortamına erişim için DISPLAY ayarlanır
        env = os.environ.copy()
        if "DISPLAY" not in env:
            env["DISPLAY"] = ":0"
        
        subprocess.run(
            ["notify-send", "-i", icon, title, message],
            env=env,
            check=False
        )
    except Exception as e:
        print(f"Bildirim gönderilemedi: {e}")

def get_mount_point(device_node):
    """Aygıtın bağlı olduğu dizini (mount point) bulur."""
    for part in psutil.disk_partitions(all=True):
        if part.device == device_node:
            return part.mountpoint, part.fstype
    return None, None

def handle_usb_event(device):
    device_node = device.device_node
    
    # Sistemin otomatik mount etmesi için kısa bekleme
    time.sleep(2)
    
    mount_point, fstype = get_mount_point(device_node)
    
    if not mount_point:
        for part in psutil.disk_partitions(all=True):
            if part.device.startswith(device_node):
                device_node = part.device
                mount_point = part.mountpoint
                fstype = part.fstype
                break

    volume_name = device.get('ID_FS_LABEL', 'İsimsiz Bellek')
    if not fstype:
        fstype = device.get('ID_FS_TYPE', 'Bilinmiyor')

    if mount_point:
        try:
            usage = psutil.disk_usage(mount_point)
            total = bytes_to_gb(usage.total)
            used = bytes_to_gb(usage.used)
            free = bytes_to_gb(usage.free)
            percent = usage.percent

            title = f"🔌 USB Takıldı: {volume_name}"
            message = (
                f"🏷️ Dosya Sistemi: {fstype}\n"
                f"💾 Toplam: {total} GB\n"
                f"🔴 Dolu: {used} GB (%{percent})\n"
                f"🟢 Boş: {free} GB"
            )
            send_notification(title, message)
        except Exception as e:
            send_notification("USB Okuma Hatası", f"Disk bilgileri okunamadı: {e}")
    else:
        send_notification("🔌 USB Takıldı", f"Aygıt: {volume_name}\nDosya Sistemi: {fstype}\n(Otomatik bağlanmadı)")

def main():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block', device_type='partition')

    for device in iter(monitor.poll, None):
        if device.action == 'add' and device.get('ID_BUS') == 'usb':
            handle_usb_event(device)

if __name__ == '__main__':
    main()
