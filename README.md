<div align="center">
    <h1>OverburstC2 based on SentinelaNet</h1>
    <h3>SentinelaNet porem melhorado!</h3>

  <p align="center">
      <img src="https://github.com/user-attachments/assets/cadc2e29-6d15-4e1a-b70b-639ae325d7d8">
  </p>
  <p>Esta Botnet é uma versão melhorada do SentinelaNet e está disponibilizada publicamente e de forma gratuita.</p>

</div>

---

<div align="center">

  ### Admin/root Commands
  Command | Description
  --------|------------
  !user   | Add/List/Remove users
  !blacklist | Add/List/Remove blacklisted targets
    
  ### CNC Commands
  Command | Description
  --------|------------
  help, ? | Shows list of commands
  botnet | Shows list of botnet attack methods
  bots | Shows all conected bots
  stop  | Stop all your floods in progress
  clear, cls | Clears the console window screen
  exit, logout | Disconnects from the C&C server

  ### Attack Commands
  Command  | Usage | Description
  ---------|-------|-------------
  .UDP     | \<target> \<port> \<time> | Starts UDP Flood 
  .TCP     | \<target> \<port> \<time> | Starts TCP Flood 
  .MIX     | \<target> \<port> \<time> | Starts TCP and UDP Flood Bypass
  .SYN     | \<target> \<port> \<time> | Starts TCP SYN Flood
  .VSE     | \<target> \<port> \<time> | Send Valve Source Engine Protocol
  .FIVEM   | \<target> \<port> \<time> | Send FiveM Status Ping Protocol
  .OVHTCP  | \<target> \<port> \<time> | Starts OVH TCP Flood Bypass
  .OVHUDP  | \<target> \<port> \<time> | Starts OVH UDP Flood Bypass
  .DISCORD | \<target> \<port> \<time> | Sends a specialized UDP packet designed to Discord
</div>

⚠️ **Nota:** Este projeto é apenas para fins educacionais e de pesquisa. O uso indevido pode ser ilegal e resultar em penalidades legais. Sempre utilize conhecimento de segurança para proteger sistemas, não para atacá-los.

<br>

---

### Novidades ✨
- Atualizado CNC
    - Adicionado blacklist ```01/03/2025```
    - Atulizado comando bots ```02/05/2025```
        - Agora o comando `bots` exibe a quantidade de bots atualmente conectados ao C2, e organizados por arquitetura do sistema (por exemplo: `x86_64`, `arm`, `mips`) (**também mostra a quantidade em cada arquitetura**).
    - Comando STOP adicionado ```09/05/2025```

- Atualizado Payload
    - Atualizado Browser Flood ```01/03/2025```
    - Atualizado UDP Flood Bypass ```06/03/2025```
    - Atualizado UDP Flood removed ```06/03/2025```
    - Adicionado TCP and UDP Flood Bypass ```07/03/2025```
    - Atualizado SYN Flood ```07/03/2025```
    - Adicionado OVHUDP and OVHTCP Flood Bypass ```04/05/2025```
    - OVH BUILDER Fixed ```09/05/2025```
---

### Owner
- **Discord: Cirqueira**
  
<a href="https://www.instagram.com/cirqueirax/"><img src="https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram"></a>
