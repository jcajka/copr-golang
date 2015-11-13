#! /bin/bash
# dont choke on github generated tarballs, rename folder to go
mkdir go && tar --strip-components 1 -C go -xzf $1
cat ./go/src/compress/testdata/Mark.Twain-Tom.Sawyer.txt |tail -n +25 | head -n 8465 > ./go/src/compress/testdata/Mark.Twain-Tom.Sawyer.txt.new
mv ./go/src/compress/testdata/Mark.Twain-Tom.Sawyer.txt.new ./go/src/compress/testdata/Mark.Twain-Tom.Sawyer.txt
rm $1
tar -czf $1 ./go
rm -rf ./go
