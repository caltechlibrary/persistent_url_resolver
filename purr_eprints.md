
# purr_eprints.py

For EPrints respositories we can use a simple SQL program
and the MySQL client to generate a local CSV file mapping
the Resolver ids (id_number in EPrints) to their target 
record urls.

Example SQL for `purr_caltechthesis.sql`

```sql
    --
    -- Run this script from remote system using the --batch option 
    -- to generate a Tab delimited version of output.
    --
    USE caltechthesis;
    SELECT id_number AS resolver_id, 
      CONCAT('https://thesis.library.caltech.edu/', eprintid) AS target_url 
      FROM eprint WHERE eprint_status = 'archive';
```

Each machine which runs the eprints repository will need a service
account that can run the command bmysql --batch < PURR_SCRIPT.SQL` where
"PURR_SCRIPT.sql" is the filename that contains the select command
to the generate tab delimited report of `resolver_id` and
`target_url`.

```bash
    ./purr_eprints.py 'serviceaccount@thesis.example.edu' './purr_thesis.sql' 'purr_thesis.csv'
```


