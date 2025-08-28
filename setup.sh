#!/bin/bash
# Script de instalación y configuración para Debian mínimo
# Ejecutar como root después de instalar Debian sin entorno gráfico

# ==========================
# CONFIGURACIÓN
# ==========================
USUARIO="gaston"
HOME_DIR="/home/$USUARIO"
SCRIPT_PATH="$HOME_DIR/loc_circuit.py"

# ==========================
# INSTALACIÓN DE PAQUETES
# ==========================
apt update
apt install -y sudo python3 python3-pip python3-opencv python3-serial \
               xorg openbox unclutter

# ==========================
# CONFIGURAR SUDO
# ==========================
usermod -aG sudo $USUARIO

# ==========================
# ACCESO A PUERTO SERIE
# ==========================
usermod -aG dialout $USUARIO

# ==========================
# CONFIGURAR GRUB
# ==========================
sed -i 's/^GRUB_TIMEOUT=.*/GRUB_TIMEOUT=0/' /etc/default/grub
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet splash"/' /etc/default/grub
if ! grep -q '^GRUB_BACKGROUND=""' /etc/default/grub; then
    echo 'GRUB_BACKGROUND=""' >> /etc/default/grub
fi
update-grub

# ==========================
# AUTOLOGIN EN TTY1
# ==========================
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat <<EOF >/etc/systemd/system/getty@tty1.service.d/override.conf
[Service]
ExecStart=
ExecStart=-/usr/sbin/agetty --autologin $USUARIO --noclear %I linux
EOF

systemctl daemon-reexec

# ==========================
# AUTOEJECUCIÓN DE startx
# ==========================
PROFILE="$HOME_DIR/.profile"
if ! grep -q "exec startx" "$PROFILE"; then
cat <<'EOF' >> "$PROFILE"

# Inicia X automáticamente en tty1
if [[ -z $DISPLAY ]] && [[ $(tty) == /dev/tty1 ]]; then
    exec startx
fi
EOF
fi
chown $USUARIO:$USUARIO "$PROFILE"

# ==========================
# CREAR ~/.xinitrc
# ==========================
XINITRC="$HOME_DIR/.xinitrc"
cat <<EOF > "$XINITRC"
#!/bin/bash
# Desactiva el salvapantallas y el apagado del monitor
xset s off
xset -dpms
xset s noblank
#unclutter -idle 0 &  # oculta el puntero si no se mueve
sleep 1
python3 $SCRIPT_PATH &
exec openbox-session
EOF

chown $USUARIO:$USUARIO "$XINITRC"
chmod +x "$XINITRC"

# ==========================
# COPIAR SCRIPTS loc_circuit.py y font.py
# ==========================
if [[ -f "loc_circuit.py" && -f "font.py" ]]; then
    cp loc_circuit.py font.py "$HOME_DIR"/
    chown $USUARIO:$USUARIO "$HOME_DIR/loc_circuit.py" "$HOME_DIR/font.py"
    echo ">>> Se copiaron loc_circuit.py y font.py a $HOME_DIR"
else
    echo ">>> ⚠️ No se encontraron loc_circuit.py y font.py en la carpeta actual."
fi

# ==========================
# CONFIGURAR SUDO PARA APAGADO SIN CONTRASEÑA
# ==========================
echo "$USUARIO ALL=(ALL) NOPASSWD: /sbin/shutdown" | EDITOR='tee -a' visudo

echo "==========================================="
echo " Instalación y configuración completada. "
echo " Reinicia el sistema para probar. "
echo "==========================================="

