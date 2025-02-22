#!/usr/bin/env python3
import os
import subprocess
import sys
import wifi_info as wifi_info_value

# 사용자가 직접 변경할 WiFi 설정
WIFI_SSID = wifi_info_value.WIFI_SSID 
WIFI_PASSWORD = wifi_info_value.WIFI_PASSWORD
WIFI_COUNTRY = wifi_info_value.WIFI_COUNTRY

def run_command(command):
    """명령어를 실행하고 오류 발생 시 종료합니다."""
    print(f"실행: {command}")
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"명령어 실행 실패: {command}")
        sys.exit(1)

def configure_features():
    # SSH 활성화
    run_command("raspi-config nonint do_ssh 0")
    # VNC 활성화
    run_command("raspi-config nonint do_vnc 0")
    # I2C 활성화
    run_command("raspi-config nonint do_i2c 0")
    # SPI 활성화
    run_command("raspi-config nonint do_spi 0")
    print("기본 기능 설정이 완료되었습니다. 변경 사항을 적용하려면 재부팅하세요.")

def reconfigure_partitions(device):
    print("경고: 파티션 재설정은 데이터 손실을 초래합니다!")
    # confirm = input("정말로 파티션을 재설정하시겠습니까? (y/N): ")
    # if confirm.lower() != 'y':
    #     print("파티션 재설정 작업을 취소합니다.")
    #     return

    # 사용 중인 파티션 언마운트 (오류 발생시 무시)
    run_command(f"umount {device}p1 || true")
    run_command(f"umount {device}p2 || true")

    # 기존 파티션 테이블 삭제 후 새로 작성 (msdos 형식)
    run_command(f"parted -s {device} mklabel msdos")

    # 부트 파티션 생성: 1MiB부터 256MiB까지 (FAT32)
    run_command(f"parted -s {device} mkpart primary fat32 1MiB 256MiB")

    # 루트 파티션 생성: 256MiB부터 디스크 끝까지 (ext4)
    run_command(f"parted -s {device} mkpart primary ext4 256MiB 100%")

    # 각 파티션에 파일 시스템 생성
    run_command(f"mkfs.vfat {device}p1")
    run_command(f"mkfs.ext4 {device}p2")

    print("파티션 재설정 및 포맷이 완료되었습니다.")

def configure_wifi(ssid, password, country):
    print("WiFi 설정을 진행합니다.")
    # print("경고: 현재 설정된 WiFi 정보는 덮어쓰게 됩니다!")
    # confirm = input("정말로 WiFi 설정을 강제로 적용하시겠습니까? (y/N): ")
    # if confirm.lower() != 'y':
    #     print("WiFi 설정을 건너뜁니다.")
    #     return

    config_content = f"""ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev update_config=1 country={country} network={{ssid="{ssid}" psk="{password}" key_mgmt=WPA-PSK}}"""
    try:
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
            f.write(config_content)
        print("WiFi 설정 파일을 업데이트했습니다.")
    except Exception as e:
        print(f"WiFi 설정 파일 업데이트 실패: {e}")
        sys.exit(1)
    
    # WiFi 재적용 (인터페이스 이름이 wlan0인 경우)
    run_command("wpa_cli -i wlan0 reconfigure")
    print("WiFi 설정이 적용되었습니다.")

def main():
    # root 권한 확인
    if os.geteuid() != 0:
        print("이 스크립트는 sudo 권한으로 실행되어야 합니다.")
        sys.exit(1)

    # 기본 기능 설정 실행 (SSH, VNC, I2C, SPI)
    configure_features()

    # '--wifi' 플래그가 있으면 WiFi 설정 실행
    if '--wifi' in sys.argv:
        configure_wifi(WIFI_SSID, WIFI_PASSWORD, WIFI_COUNTRY)

    # '--partition' 플래그가 있으면 파티션 재설정 실행
    if '--partition' in sys.argv:
        # 기본 디바이스 경로 (필요시 수정)
        device = "/dev/mmcblk0"
        reconfigure_partitions(device)

if __name__ == "__main__":
    main()
