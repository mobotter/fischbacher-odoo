#1 zbsync_sql

Starting an MS SQL Server:

```
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=passwort" -p 1433:1433  --name sqlpreview --hostname sqlpreview -d mcr.microsoft.com/mssql/server:2022-preview-ubuntu-22.04
```

#2 Contributors

- Marc Wimmer <marc@zebroo.de>
