#!/bin/bash 
appname="EyeTracker"
dir=$(pwd)
pyinstaller -y --clean --windowed --name ${appname}  --exclude-module _tkinter   --exclude-module Tkinter   --exclude-module enchant   --exclude-module twisted ./kivy/main.py 

perl -pi -e "s|exe,|exe,Tree(\"$dir/kivy/\"),|g" ${appname}.spec

pyinstaller -y --clean --windowed ${appname}.spec
pushd dist
hdiutil create ./${appname}.dmg -srcfolder ${appname}.app -ov
popd