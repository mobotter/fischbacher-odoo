#1 zbsync_ftp

Start test ftp server:

FTP Server:

```
docker run -d \
    -p 21:21 \
    -p 21000-21010:21000-21010 \
    -e USERS="one|1234" \
    -e ADDRESS=ftp.site.domain \
    delfer/alpine-ftp-server
```

SFTP-Server:

```
docker run -p 22:22 -d atmoz/sftp foo:pass:::upload
```

#2 Contributors

- Marc Wimmer <marc@itewimmer.de>
