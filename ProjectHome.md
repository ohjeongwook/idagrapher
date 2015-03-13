IDA is a commercial reverse engineering tool which has disassembly and debugging functionalities. It has pretty nice graph based disassembly browser. But, it fails sometimes when it meets some severe obfuscation. This usually happens with malware.

IDAGrapher is a project to visualize the code chunks in a way that it doesn't break even though it's obfuscated and tweaked using many different way to fool disassembler. It still relies on the power of IDA, but it has it's own logic to determine and draw the graphs.

And the point is it's an opensource project and you can modify the logic whenever you need to and contribute and feedback the result to the project and you can make it more stable and powerful.


![http://idagrapher.googlecode.com/svn/trunk/Docs/Sample.png](http://idagrapher.googlecode.com/svn/trunk/Docs/Sample.png)