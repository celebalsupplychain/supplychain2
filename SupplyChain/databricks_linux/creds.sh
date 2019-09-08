#!/usr/bin/expect -f

/bin/bash -c source activate /home/site/wwwroot/antenv/bin/activate;
set hostname [lindex $argv 0];
set token [lindex $argv 1];
 
set timeout -1

 
spawn /home/site/wwwroot/antenv/bin/databricks configure --token
 
expect "Databricks Host (should begin with https://): "
 
send -- "$hostname\n"

expect "Token: "

send -- "$token\n"


expect eof
