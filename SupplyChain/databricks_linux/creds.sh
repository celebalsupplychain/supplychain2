#!/usr/bin/expect -f

set hostname [lindex $argv 0];
set token [lindex $argv 1];
 
set timeout -1
 
spawn databricks configure --token
 
expect "Databricks Host (should begin with https://): "
 
send -- "$hostname\n"

expect "Token: "

send -- "$token\n"


expect eof
