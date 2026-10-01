import platform
import json
import os

def read_file(path):
  try:
    with open(path) as f:
      return f.read()
  except OSError:
    return None


class OperatingSystem:
  def __init__(self):
    self.info = {}

  def get_extra(self): return {}

  def get_cpu_cores(self): return os.cpu_count()

  def get_os_name(self): return platform.system()

  def get_version(self): return platform.version()

  def get_release(self): return platform.release()

  def get_architecture(self): return platform.machine()

  def get_hostname(self): return platform.node()

  def get_py_version(self): return platform.python_version()

  def get_cpu_model(self): return platform.processor() or None

  def collect(self):
    self.info = {
      "os": self.get_os_name(),
      "release": self.get_release(),
      "version": self.get_version(),
      "architecture": self.get_architecture(),
      "hostname": self.get_hostname(),
      "cpu_model": self.get_cpu_model(),
      "cpu_cores": self.get_cpu_cores(),
      "py_version": self.get_py_version(),
    }
    self.info.update(self.get_extra())
    return self.info

  @staticmethod
  def field(text, key, sep=":"):
    for line in text.splitlines():
      if line[:len(key)] == key:
        return line.split(sep, 1)[1].strip().strip('"')


class LinuxOS(OperatingSystem):
  def __init__(self):
    super().__init__()
    self.cpu_info = read_file("/proc/cpuinfo") or ""
    self.mem_info = read_file("/proc/meminfo") or ""
    self.os_release = read_file("/etc/os-release") or ""
    self.uptime = read_file("/proc/uptime") or ""
    self.product_name = read_file("/sys/class/dmi/id/product_name") or ""
    self.manufacturer = read_file("/sys/class/dmi/id/sys_vendor") or ""
    try:
      self.count_proc = os.listdir("/proc")
    except OSError:
      self.count_proc = []

  @staticmethod
  def check_int(string):
    num = "1234567890"
    for i in string:
      if i not in num:
        return 0
    return 1

  def get_distr(self):
    return self.field(self.os_release, "PRETTY_NAME", "=")

  def get_ram_total(self):
    return self.field(self.mem_info, "MemTotal")

  def get_ram_free(self):
    return self.field(self.mem_info, "MemAvailable")

  def get_uptime(self):
    if not self.uptime.split(): return None
    return float(self.uptime.split()[0])

  def get_count_proc(self):
    cnt = 0
    for i in self.count_proc:
      if self.check_int(i):
        cnt += 1
    return cnt

  def get_manufacturer(self):
    return self.manufacturer.strip() or None

  def get_product_name(self):
    return self.product_name.strip() or None

  def get_cpu_model(self):
    return self.field(self.cpu_info, "model name") or super().get_cpu_model()

  def get_extra(self):
    return {
      "distribution": self.get_distr(),
      "ram_total": self.get_ram_total(),
      "ram_free": self.get_ram_free(),
      "uptime": self.get_uptime(),
      "count_proc": self.get_count_proc(),
      "manufacturer": self.get_manufacturer(),
      "product_name": self.get_product_name()
    }


class WindowsOS(OperatingSystem):
  def __init__(self):
    super().__init__()
    import winreg
    self.winreg = winreg
    self.win_ver = self.get_win_version()

  def get_manufacturer(self):
    path = r"HARDWARE\DESCRIPTION\System\BIOS"
    return self.reg_value(path, "SystemManufacturer")

  def get_product_name(self):
    path = r"HARDWARE\DESCRIPTION\System\BIOS"
    return self.reg_value(path, "SystemProductName")

  def get_date_install(self):
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    return self.reg_value(path, "InstallDate")

  def reg_value(self, path, name):
    try:
      with self.winreg.OpenKey(self.winreg.HKEY_LOCAL_MACHINE, path) as key:
        return self.winreg.QueryValueEx(key, name)[0]
    except OSError:
      return None

  def get_cpu_model(self):
    cpu = self.reg_value(r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
                         "ProcessorNameString")
    return cpu.strip() if cpu else super().get_cpu_model()

  def get_win_version(self): return platform.win32_ver()

  def get_win_edition(self): return platform.win32_edition()

  def get_extra(self):
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    return {
      "windows_release": self.win_ver[0],
      "windows_version": self.win_ver[1],
      "windows_edition": self.get_win_edition(),
      "windows_display_version": self.reg_value(path, "DisplayVersion"),
      "windows_build": self.reg_value(path, "CurrentBuild"),
      "manufacturer": self.get_manufacturer(),
      "product_name": self.get_product_name(),
      "date_install": self.get_date_install(),
    }


class MacOS(OperatingSystem):
  def __init__(self):
    super().__init__()
    self.mac_ver = self.get_mac_version()

  def get_mac_version(self): return platform.mac_ver()[0]

  def get_extra(self):
    return {
      "macos_version": self.mac_ver
    }


def get_os():
  operating_system = {
    "Linux": LinuxOS,
    "Windows": WindowsOS,
    "Darwin": MacOS
  }
  system = platform.system()
  os_class = operating_system.get(system, OperatingSystem)
  return os_class()


def main():
  info = get_os().collect()
  file_name = "sys_config.json"
  with open(file_name, "w") as f:
    json.dump(info, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
  main()