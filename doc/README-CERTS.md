# Generar Certificados

#######################
# 1) Crear la CA raíz #
#######################
# Clave privada (4096 bits, cifrada con passphrase)
```
openssl genrsa -aes256 -out ca.key 4096
```

# Certificado raíz autofirmado válido 10 años
```
openssl req -x509 -new -key ca.key -sha256 -days 3650 \
  -out ca.crt \
  -subj "/C=ES/O=MiLab MQTT/CN=MiLab MQTT Root CA"
```
############################################
# 2) Crear la clave privada del BROKER     #
#    (nombre EXACTO que pide Mosquitto:    #
#     cert.key)                            #
############################################
```
openssl genrsa -out cert.key 2048
```
############################################
# 3) Generar la CSR del broker con SAN     #
############################################

```
cat > san.cnf <<'EOF'
[ req ]
distinguished_name = subj
prompt             = no
req_extensions     = san

[ subj ]
C  = ES
O  = MiLab MQTT
CN = mosquito_dev            # ⇦ cambia por tu FQDN

[ san ]
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = mqtt.local         # ⇦ FQDN adicional
IP.1  = 192.168.1.50       # ⇦ IP del broker
EOF

openssl req -new -key cert.key -out cert.csr -config san.cnf
```
######################################################
# 4) Firmar la CSR con la CA → cert.crt del broker   #
######################################################
```
openssl x509 -req -in cert.csr -CA ca.crt -CAkey ca.key \
  -CAcreateserial -out cert.crt \
  -days 825 -sha256 -extfile san.cnf -extensions san
```
####################################
# 5) Comprobar que ya existen los  #
#    tres ficheros solicitados     #
####################################
```
ls -l ca.crt cert.crt cert.key
```


Meter en mosquitto/config/ctx y app/ctx/dev