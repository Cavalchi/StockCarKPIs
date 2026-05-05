# O que é o Docker e por que usamos? 🐋

Se você nunca usou Docker, não se preocupe! Ele é uma das ferramentas mais importantes hoje na Engenharia de Dados e Desenvolvimento de Software.

## Pra que serve o Docker?
Sabe quando alguém diz *"na minha máquina funciona"*? O Docker resolve isso.
Ele empacota o software (no nosso caso, o banco de dados **PostgreSQL**) dentro de uma "caixa" isolada chamada **Container**. 

Isso significa que você não precisa baixar o instalador do PostgreSQL, configurar portas, criar usuários manualmente ou poluir o seu Windows. O Docker faz o download de um "computadorzinho virtual" focado apenas em rodar o banco de dados, com tudo já configurado através do arquivo `docker-compose.yml`.

## Como usar no Windows?

1. **Baixar o Docker Desktop:**
   Acesse [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/) e baixe a versão para Windows.
2. **Instalar:**
   Dê "Next" em tudo. É possível que ele peça para instalar uma funcionalidade do Windows chamada **WSL 2** (Windows Subsystem for Linux). Isso é normal e super recomendado, basta aceitar.
3. **Reiniciar o PC:**
   Pode ser necessário reiniciar o computador após a instalação.
4. **Abrir o Docker Desktop:**
   Procure por "Docker Desktop" no menu Iniciar e deixe o aplicativo aberto (um ícone de baleia vai aparecer perto do seu relógio).
5. **Rodar o Banco de Dados:**
   Abra o seu terminal (PowerShell ou VSCode), vá até a pasta deste projeto (`StockCarKPIs`) e digite:
   ```bash
   docker-compose up -d
   ```
   
**Pronto!** O Docker vai baixar o PostgreSQL oficial, criar o banco, rodar o nosso arquivo `schema.sql` (para criar as tabelas) e liberar a porta `5432` para o Python conectar. Quando você não quiser mais usar, basta digitar `docker-compose down` e ele "desliga" o banco.
