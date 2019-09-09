def func(hostname,token,n):
     try:
         child = pexpect.popen_spawn.PopenSpawn('databricks configure --token',timeout=n)
         child.expect_exact(b'Databricks Host (should begin with https://):')
         child.sendline(bytes('{}'.format(hostname),'utf-8'))
         child.expect_exact(b'Token: ')
         child.sendline(bytes('{}'.format(token),'utf-8'))
     except:
        n=n+1
        func(hostname,token,n)
import pexpect
import sys
from pexpect import popen_spawn
hostname=sys.argv[1]
token=sys.argv[2]
func(hostname,token,1)
