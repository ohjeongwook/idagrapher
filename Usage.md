# Introduction #

This is a simple notes how you can use the script.

# Details #

Here's how you can use this script:
  * You need to install IDAPython if you don't have it installed or have it by default.

  * Download and install graphviz package from http://www.graphviz.org

  * Just download and copy IDAGrapher.py from the source page.

  * Run the script from IDAPython(Alt-9).

  * The script will ask the path for saving the result.

  * It will create .dot and .png file. It will try to launch default graphics viewer to show the png file when the analysis is done.

  * Don't try to run this script with huge amount of code inside it. This script is currently for polymorphed binaries with relatively small size of polymorphic bootstrap code.