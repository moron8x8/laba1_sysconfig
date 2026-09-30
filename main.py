import platform
import json


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
      "py_version": self.get_py_version(),
    }
    self.info.update(self.get_extra())
    return self.info

class LinuxOS(OperatingSystem):
  def __init__(self):
    super().__init__()
    self.cpu_info = read_file("/proc/cpuinfo") or ""
    self.mem_info = read_file("/proc/meminfo") or ""
    self.os_release = read_file("/etc/os-release") or ""
    self.uptime = read_file("/proc/uptime") or ""

  def get_cpu_model(self):
    for line in self.cpu_info.splitlines():
      l = len("model name")
      if line[:l] == "model name":
        return line.split(":", 1)[1].strip()

  def get_cpu_cores(self):
    for line in self.cpu_info.splitlines():
      l = len("cpu cores")
      if line[:l] == "cpu cores":
        return line.split(":", 1)[1].strip()

  def get_distr(self):
    for line in self.os_release.splitlines():
      l = len("PRETTY_NAME")
      if line[:l] == "PRETTY_NAME":
        return line.split("=", 1)[1].strip().strip('"')

  def get_ram_total(self):
    for line in self.mem_info.splitlines():
      l = len("MemTotal")
      if line[:l] == "MemTotal":
        return line.split(":", 1)[1].strip().strip('"')

  def get_ram_free(self):
    for line in self.mem_info.splitlines():
      l = len("MemFree")
      if line[:l] == "MemFree":
        return line.split(":", 1)[1].strip().strip('"')

  def get_uptime(self):
    if not self.uptime.split(): return None
    return float(self.uptime.split()[0])

  def get_extra(self):
    return {
      "distribution": self.get_distr(),
      "cpu_model": self.get_cpu_model(),
      "cpu_cores": self.get_cpu_cores(),
      "ram_total": self.get_ram_total(),
      "ram_free": self.get_ram_free(),
      "uptime": self.get_uptime(),
    }

class WindowsOS(OperatingSystem):
  def __init__(self):
    super().__init__()
    self.win_ver = self.get_win_version()

  def get_extra(self):
    return {
      "windows_release": self.win_ver[0],
      "windows_build": self.win_ver[1],
      "windows_edition": self.get_win_edition(),
    }

  def get_win_version(self): return platform.win32_ver()
  def get_win_edition(self): return platform.win32_edition()


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