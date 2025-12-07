# Raspberry Pi 5 (4GB RAM) - SanDisk SD Card Setup Guide

This guide covers setting up a SanDisk SD card for Raspberry Pi 5 with 4GB RAM, including OS installation and initial configuration for the IoT Secure Water Monitor project.

## Prerequisites

- **Raspberry Pi 5** (4GB RAM model)
- **SanDisk SD Card** (minimum 16GB, Class 10 or better, recommended: 32GB+)
- **Computer** (Windows/Mac/Linux) with SD card reader
- **MicroSD to SD adapter** (if needed)
- **Internet connection** (for downloading Raspberry Pi OS)

## Step 1: Choose the Right SD Card

### Recommended SanDisk Models:
- **SanDisk Ultra** (32GB/64GB) - Good balance of speed and price
- **SanDisk Extreme** (32GB/64GB) - Faster, better for intensive workloads
- **SanDisk Extreme Pro** - Best performance for demanding applications

### Minimum Requirements:
- **Capacity**: 16GB minimum (32GB+ recommended)
- **Speed**: Class 10 or UHS-I (U3 recommended)
- **Format**: microSDHC or microSDXC

### Is 32GB Enough? ✅ YES!

For your IoT Water Monitor project, **32GB is more than sufficient**. Here's the storage breakdown:

**Typical Storage Usage:**
- **Raspberry Pi OS (64-bit)**: ~3-4 GB
- **System files & updates**: ~2-3 GB
- **Python & dependencies** (requests, pycryptodome): ~100-200 MB
- **Your project files** (scripts, keys): ~10-50 MB
- **Logs & temporary files**: ~500 MB - 1 GB
- **Buffer space**: ~5-10 GB

**Total estimated usage**: ~10-15 GB out of 32GB

**32GB provides:**
- ✅ Plenty of room for OS and system updates
- ✅ Space for multiple projects
- ✅ Room for logs and temporary files
- ✅ Comfortable buffer for future growth

**Consider 64GB+ if:**
- You plan to store large amounts of sensor data locally
- You'll run multiple heavy applications
- You want extra headroom for years of updates
- You're doing video/image processing

**For this IoT project, 32GB is perfect!** 🎯

## Step 2: Download Raspberry Pi OS

1. **Visit Raspberry Pi Imager**:
   - Download from: https://www.raspberrypi.com/software/
   - Or direct download: https://downloads.raspberrypi.org/imager/imager_latest.exe (Windows)

2. **Alternative: Download OS Image Directly**:
   - Visit: https://www.raspberrypi.com/software/operating-systems/
   - Choose **Raspberry Pi OS (64-bit)** - recommended for Pi 5
   - Download the `.img.xz` file (approximately 1.5GB)

## Step 3: Install Raspberry Pi Imager

### Windows:
1. Download `imager_latest.exe` from Raspberry Pi website
2. Run the installer
3. Follow installation wizard

### Mac:
1. Download `.dmg` file
2. Open and drag to Applications folder

### Linux:
```bash
sudo apt update
sudo apt install rpi-imager
```

## Step 4: Write OS to SD Card

### Using Raspberry Pi Imager (Recommended):

1. **Insert SD Card** into your computer's card reader

2. **Open Raspberry Pi Imager**

3. **Click "CHOOSE OS"**:
   - Select **Raspberry Pi OS (64-bit)** (recommended for Pi 5)
   - Or choose **Raspberry Pi OS (other)** → **Raspberry Pi OS (64-bit)** → **Raspberry Pi OS (Legacy)** if needed

4. **Click "CHOOSE STORAGE"**:
   - Select your SanDisk SD card
   - ⚠️ **WARNING**: Make sure you select the correct drive!

5. **Click the gear icon** (⚙️) to configure advanced options:
   - **Enable SSH**: ✅ Check this box
   - **Set username**: `pi` (or your preferred username)
   - **Set password**: Choose a strong password
   - **Configure wireless LAN**: Enter your WiFi SSID and password
   - **Set locale settings**: Choose your timezone
   - **Enable public key authentication**: Optional (for advanced users)

6. **Click "WRITE"**:
   - Confirm the warning
   - Wait for the process to complete (5-15 minutes depending on card speed)

### Using Command Line (Alternative):

#### Windows (PowerShell):
```powershell
# Download Raspberry Pi OS image first
# Extract .img.xz file using 7-Zip or similar

# Use Raspberry Pi Imager CLI or Win32DiskImager
# Download Win32DiskImager from: https://sourceforge.net/projects/win32diskimager/
```

#### Linux/Mac:
```bash
# Extract image
xz -d raspios-*.img.xz

# Write to SD card (replace /dev/sdX with your SD card device)
# ⚠️ WARNING: Double-check the device name!
sudo dd if=raspios-*.img of=/dev/sdX bs=4M status=progress conv=fsync
```

## Step 5: Verify SD Card

After writing:

1. **Eject SD card safely** from your computer
2. **Re-insert** to verify it was written correctly
3. **Check contents**:
   - Windows: Should see `boot` folder
   - Mac/Linux: Should see FAT32 partition

## Step 6: First Boot Setup

1. **Insert SD card** into Raspberry Pi 5
2. **Connect peripherals**:
   - HDMI cable to monitor/TV
   - USB keyboard and mouse
   - Ethernet cable (or use WiFi if configured)
   - Power supply (USB-C, 5V 5A minimum for Pi 5)

3. **Power on** the Raspberry Pi 5

4. **First boot** will take 2-5 minutes:
   - System will expand filesystem automatically
   - WiFi will connect (if configured)
   - System will update (if internet available)

5. **Complete setup wizard** (if shown):
   - Set country/locale
   - Change password (if not set in Imager)
   - Update software
   - Reboot when prompted

## Step 7: Initial Configuration

### Enable SSH (if not already enabled):

```bash
# On Raspberry Pi, open terminal
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Update System:

```bash
sudo apt update
sudo apt upgrade -y
sudo reboot
```

### Install Essential Tools:

```bash
sudo apt install -y git python3-pip vim
```

## Step 8: Verify SD Card Performance

Test your SanDisk SD card speed:

```bash
# Write speed test
sudo dd if=/dev/zero of=testfile bs=1M count=100 conv=fdatasync
# Note the speed (MB/s)

# Read speed test
sudo dd if=testfile of=/dev/null bs=1M count=100
# Note the speed (MB/s)

# Clean up
rm testfile
```

**Expected speeds for SanDisk Ultra**:
- Write: 20-30 MB/s
- Read: 40-80 MB/s

**Expected speeds for SanDisk Extreme**:
- Write: 40-60 MB/s
- Read: 80-100 MB/s

## Step 9: Prepare for Water Monitor Project

### Create Project Directory:

```bash
mkdir -p ~/water-monitor
cd ~/water-monitor
```

### Install Python Dependencies:

```bash
# Install required packages
pip3 install requests pycryptodome

# Or create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install requests pycryptodome
```

### Transfer Project Files:

From your development machine:

```bash
# Using SCP (replace with your Pi's IP)
scp raspberry_pi_client.py encryption_utils.py pi@raspberrypi.local:~/water-monitor/
scp -r keys/public.pem pi@raspberrypi.local:~/water-monitor/keys/
scp -r sensor_keys/ pi@raspberrypi.local:~/water-monitor/
```

## Troubleshooting

### SD Card Not Recognized:
- Try different card reader
- Check if card is locked (physical switch on adapter)
- Format card as FAT32 and try again
- Test card in another device

### Boot Issues:
- **Red LED only**: Power issue - use official Pi 5 power supply (5V 5A)
- **No display**: Check HDMI cable, try different port
- **Corrupted boot**: Re-write OS image to SD card

### Slow Performance:
- Use faster SD card (SanDisk Extreme or Extreme Pro)
- Check if card is genuine (counterfeit cards are slower)
- Enable overclocking (advanced users only):
  ```bash
  sudo nano /boot/config.txt
  # Add: over_voltage=2
  # Add: arm_freq=2000
  ```

### SD Card Corruption:
- Always shut down properly: `sudo shutdown -h now`
- Use `sync` before removing power
- Consider using read-only filesystem for production (advanced)

## SD Card Maintenance

### Check Filesystem:

```bash
sudo fsck -f /dev/mmcblk0p2
```

### Check Disk Space:

```bash
df -h
```

### Clean Up:

```bash
# Remove old packages
sudo apt autoremove -y
sudo apt autoclean

# Clear logs (optional)
sudo journalctl --vacuum-time=7d
```

## Best Practices

1. **Use Quality SD Cards**: SanDisk Ultra or better
2. **Regular Backups**: 
   ```bash
   # Create backup image
   sudo dd if=/dev/mmcblk0 of=backup.img bs=4M status=progress
   ```
3. **Proper Shutdown**: Always use `sudo shutdown -h now`
4. **Monitor Health**: Check SD card health regularly
5. **Consider USB Boot**: Pi 5 supports USB boot (faster than SD)

## Next Steps

After SD card setup is complete:

1. Follow **RASPBERRY_PI_SETUP.md** for project-specific configuration
2. Transfer project files to Raspberry Pi
3. Configure sensors and test connectivity
4. Set up as a service for automatic startup

## Additional Resources

- **Raspberry Pi 5 Official Documentation**: https://www.raspberrypi.com/documentation/computers/raspberry-pi-5.html
- **Raspberry Pi Imager Guide**: https://www.raspberrypi.com/documentation/computers/getting-started.html#installing-the-operating-system
- **SanDisk SD Card Compatibility**: https://www.sandisk.com/home/memory-cards/microsd-cards

## Quick Reference

### Find Raspberry Pi IP Address:
```bash
# On Raspberry Pi
hostname -I

# Or from another computer
ping raspberrypi.local
```

### Connect via SSH:
```bash
ssh pi@raspberrypi.local
# Or
ssh pi@<pi_ip_address>
```

### Check SD Card Info:
```bash
sudo fdisk -l /dev/mmcblk0
```

---

**Note**: This guide is specifically for Raspberry Pi 5. For older models (Pi 4, Pi 3, etc.), the process is similar but power requirements differ.

