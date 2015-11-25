#! /bin/bash
# dont choke on github generated tarballs, rename folder to go
mkdir go && tar --strip-components 1 -C go -xzf $1
rm $1
tar -czf $1 ./go
rm -rf ./go
