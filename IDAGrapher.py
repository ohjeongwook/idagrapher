import idaapi
import idc
import os

class IDAAnalyzer:
	BgColor='#33339F'
	NodeColor='white'
	NodeFontColor='white'
	EdgeFontColor='white'
	EdgeColor='white'

	DebugLevel = 0
	BlockData = {}
	Map = {}
	MapHash = {}
	DOTExeList = ( r'c:\Program Files (x86)\Graphviz2.26.3\bin\dot.exe', r'c:\Program Files\Graphviz2.26.3\bin\dot.exe' )
	DOTExe = r'c:\Program Files (x86)\Graphviz2.26.3\bin\dot.exe'

	def __init__( self ):
		self.DetectDOTExe()

		if not self.DOTExe:
			return

		self.AnalyzeAllSections()
		self.CleanUpNops()
		#self.PrintAnalysisData()

	def DetectDOTExe(self):
		self.DOTExe = None
		for file in self.DOTExeList:
			if os.path.exists( file ):
				self.DOTExe = file
				break

		if not self.DOTExe:
			self.DOTExe = idaapi.askfile_c(1,"*.exe","Select dot.exe file");

		if not self.DOTExe:
			print "You need to install Graphviz. Download from http://graphviz.org"

	def AnalyzeAllSections( self ):
		BlockData = {}
		Map = []
		CurrentAddress = idc.MinEA()

		i = 0
		while i < idaapi.get_segm_qty():
			seg = idaapi.getnseg( i )
	 		self.AnalyzeRange( seg.startEA, seg.endEA )
			i+=1

	def AddToMap(self, Src, Dst, DstSymbolicName, Comment='' ):
		if type(Dst).__name__ == 'int':
			dst_str = hex( Dst )
		else:
			dst_str = str( Dst )

		if self.DebugLevel > 2:
			print Comment,':',hex(Src), "->",dst_str

		map_key = hex(Src) + ":" + dst_str
		if not self.MapHash.has_key( map_key ):
			if not self.Map.has_key( Src ):
				self.Map[Src] = []
			self.Map[Src].append(( Dst, DstSymbolicName, Comment ))
			self.MapHash[ map_key ] = 1

	def AnalyzeFunction( self, FunctionBlockAddress ):
		AddressesMap={}
		AddressesMap[FunctionBlockAddress] = 1
		Addresses =[ FunctionBlockAddress ]
		
		Calls=[]
		for Address in Addresses:
			if self.DebugLevel > 1:
				print 'Analyzing',hex(Address)
			#for line in self.BlockData[Address]:
			#	print line

			if self.Map.has_key( Address ):
				for ( dst, dst_in_symbol, comment ) in self.Map[Address]:
					if type(dst).__name__ == 'int':
						if comment != 'call' and not AddressesMap.has_key( dst ):
							if self.DebugLevel > 1:
								print hex(dst) + "(" + str(dst_in_symbol) + ")"

							Addresses.append( dst )
							AddressesMap[dst] = 1
					if comment == 'call':
						if type(dst).__name__ == 'int':
							Calls.append( dst )
						else:
							dst_str = self.GetDstStr( dst, dst_in_symbol )
							Calls.append( dst_str )

		return ( Addresses, Calls )

	def AnalyzeRange( self, startEA, endEA ):
		CurrentAddress = startEA
		CurrentBlockAddress = CurrentAddress
		NewBlockStart = True
		last_op_code = ''
		while CurrentAddress < endEA:
			if idaapi.isCode( idaapi.get_flags_novalue( CurrentAddress ) ):
				idaapi.decode_insn( CurrentAddress )
				op_code = idaapi.ua_mnem( CurrentAddress )

				operands=[]
				disasm_line = op_code + ' ' 
				for i in range(0, 6, 1):
					operand = idaapi.ua_outop2( CurrentAddress, i )
					if not operand:
						break;
					operand = idaapi.tag_remove( operand )
					operands.append( operand )
					if i != 0:
						disasm_line += ','
					disasm_line += operand
				#disasm_line = idaapi.tag_remove( idaapi.generate_disasm_line( CurrentAddress ) )

				xref = idaapi.xrefblk_t()

				ret = xref.first_to( CurrentAddress, idaapi.XREF_FAR )
				while ret:
					ret = xref.next_to()
					NewBlockStart = True

				if NewBlockStart and last_op_code[0:3] != 'ret' and last_op_code != 'new block':
					self.AddToMap( CurrentBlockAddress, CurrentAddress, None, 'link')

				if NewBlockStart:
					CurrentBlockAddress = CurrentAddress
					self.BlockData[CurrentBlockAddress]=[]
					if self.DebugLevel > 2:
						print '='*80

				if self.DebugLevel > 2:
					print hex(CurrentAddress), disasm_line
				self.BlockData[CurrentBlockAddress].append( ( CurrentAddress, disasm_line ) )

				NewBlockStart = False
				CallIsResolved = False
				ret = xref.first_from( CurrentAddress, idaapi.XREF_FAR )
				while ret:
					if xref.iscode:
						if op_code == 'jmp' and xref.to == CurrentAddress + idaapi.cvar.cmd.size:
							NewBlockStart = True
						elif op_code == 'call':
							CallIsResolved = True
							self.AddToMap( CurrentBlockAddress,xref.to, operands[0], 'call')
						else:
							if len(operands) > 0 :
								self.AddToMap( CurrentBlockAddress,xref.to, operands[0], 'from')
							NewBlockStart = True
					ret = xref.next_from()

				if ( op_code == 'call' or op_code =='' ) and not CallIsResolved:
					self.AddToMap( CurrentBlockAddress, operands[0], operands[0], 'call')

				if NewBlockStart and op_code != 'jmp':
					self.AddToMap( CurrentBlockAddress, CurrentAddress + idaapi.cvar.cmd.size, '', 'link')

				if op_code[0:3] == 'ret':
					NewBlockStart = True

				last_op_code = op_code
				CurrentAddress += idaapi.cvar.cmd.size
			else:
				CurrentAddress += 1

	def GetOutputFile(self):
		return idaapi.askfile_c(1,"*.dot","Select DOT File to Output");

	def CleanUpNops(self):
		for block_address in self.BlockData.keys():
			Array = self.BlockData[block_address]

			i = 0
			while i < len(Array)-2:
				if Array[i][1]=='push eax' and Array[i+1][1]=='bswap eax' and Array[i+2][1]=='pop eax':
					if self.DebugLevel > 2:
						print 'Clean up', i

					Array.pop(i)
					Array.pop(i)
					Array.pop(i)
				i+=1

	def GetDstStr( self, dst, dst_in_symbol ):
		dst_str = ''
		if type(dst).__name__ == 'int':
			if self.BlockData.has_key( dst ) or not dst_in_symbol:
				dst_str = hex( dst )
			else:
				dst_str = dst_in_symbol
		else:
			if dst_in_symbol:
				dst_str = dst_in_symbol
			else:
				dst_str = str( dst )
		return dst_str

	def AnalyzeFunctionRelationship(self, StartAddress):
		FunctionsMap={}
		FunctionsMap[ StartAddress ] = {}
		Functions=[ StartAddress ]

		for Function in Functions:
			(Addresses, Calls) = self.AnalyzeFunction( Function )
			for CalledFunction in Calls:
				if type(CalledFunction).__name__ == 'str' and CalledFunction[0] == 'e' and len(CalledFunction)==3: #Register
					continue

				FunctionsMap[Function][CalledFunction]=1
				if type(CalledFunction).__name__ == 'int':
					if self.DebugLevel > 2:
						print hex(Function),'->',hex(CalledFunction)
					if not FunctionsMap.has_key( CalledFunction ):
						FunctionsMap[ CalledFunction ] = {}
						Functions.append( CalledFunction )
		return FunctionsMap

	def PrintOverview( self , format = 'dot', show_assembly = True, output_format = 'png' ):
		if format == 'dot':
			filename = self.GetOutputFile()
			if filename:
				fd = open( filename, "w" )
				fd.write( 'digraph G {\r\n' )
	
				node_shape = 'rectangle'
				if show_assembly:
					node_shape = 'record'
				fd.write( '\tnode[color="'+self.NodeColor+'", fontcolor="'+self.NodeFontColor+'",shape=' + node_shape + '];\r\n' )
				fd.write( '\tedge[fontcolor="'+self.EdgeFontColor+'";color="'+self.EdgeColor+'"];\r\n' )
				fd.write( '\tbgcolor="'+self.BgColor+'"\r\n' )
	
				BranchingOutNodes={}
				for frm, tos in self.Map.iteritems():
					for ( dst, dst_in_symbol, comment ) in tos:
						if self.BlockData.has_key( frm ):
							BranchingOutNodes[frm]=1
							style_str=''
							if comment == 'call':
								style_str='[color="red"]'
		
							dst_str = self.GetDstStr( dst, dst_in_symbol )
							fd.write( "\t\"" + hex(frm) + "\" -> \"" +  dst_str + '\" ' + style_str + ';\r\n' )
	
				for block_address in self.BlockData.keys():
					style_str = ''
					if not BranchingOutNodes.has_key( block_address ):
						style_str = ' style=filled, fillcolor="#009000", fontcolor="#FFF3C3"' 
	
					disasm_lines = ''
					if show_assembly:
						disasm_lines = 'label="{' + hex(block_address) + '|'
						for (Address,Disasms) in self.BlockData[block_address]:
							disasm_lines += Disasms + '\\r\\n'
						disasm_lines += '}",'
	
					fd.write( '\t"' + hex(block_address) +'" [' + disasm_lines + ' ' + style_str + '];\r\n' )
	
				fd.write( '}\r\n' )
				fd.close()
				self.Render(filename,output_format)
	
	def Render(self, filename,output_format):
		output_filename = filename[:-4]+'.' + output_format
		cmd_line = '"' + self.DOTExe + r'" -o' + output_filename + ' -T' + output_format + ' ' + filename 
		os.popen( cmd_line )
		os.popen( output_filename )

	def GetName(self,Address):
		if type(Address).__name__ == 'int':
			Name = idaapi.get_name(Address,Address)
			if Name:
				return Name
			return hex( Address )

		return str( Address )

	def PrintFunctionRelationship( self , StartAddress, format = 'dot', output_format = 'png' ):
		FunctionsMap = self.AnalyzeFunctionRelationship( StartAddress )

		if format == 'dot':
			filename = self.GetOutputFile()
			if filename:
				fd = open( filename, "w" )
				fd.write( 'digraph G {\r\n' )
	
				node_shape = 'rectangle'
				fd.write( '\tnode[color="'+self.NodeColor+'", fontcolor="'+self.NodeFontColor+'",shape=' + node_shape + '];\r\n' )
				fd.write( '\tedge[fontcolor="'+self.EdgeFontColor+'";color="'+self.EdgeColor+'"];\r\n' )
				fd.write( '\tbgcolor="'+self.BgColor+'"\r\n' )

				Edges={}
				for SrcFunction in FunctionsMap.keys():
					SrcFunctionName=self.GetName(SrcFunction)
					Edges[SrcFunctionName]=1
					for DstFunction in FunctionsMap[SrcFunction].keys():
						DstFunctionName=self.GetName(DstFunction)
						print 'Writing',SrcFunctionName,DstFunctionName
						style_str=''							

						fd.write( "\t\"" + SrcFunctionName + "\" -> \"" +  DstFunctionName + '\" ' + style_str + ';\r\n' )
						Edges[DstFunctionName]=1

				for Edge in Edges.keys():
					if Edge[0:4]!='sub_' and Edge[0:2]!='0x' and Edge[0:6]!='dword_':
						style_str = ' style=filled, fillcolor="#009000", fontcolor="#FFF3C3"' 	
						fd.write( '\t"' + Edge +'" [ ' + style_str + '];\r\n' )
						
				fd.close()

			self.Render(filename,output_format)

	def PrintAnalysisData( self ):
		for BlockAddress in self.BlockData.keys():
			disasm_lines=''
			for (Address,Disasms) in self.BlockData[BlockAddress]:
				disasm_lines += hex(Address) + ' ' + Disasms + '\r\n'
			print '='*80
			print hex(BlockAddress)
			print disasm_lines

		for (frm,to) in self.Map:
			#print hex(frm), hex(to)
			pass

if __name__ == '__main__':
	ida_analyzer = IDAAnalyzer()
	ida_analyzer.PrintOverview( 'dot', True, 'png' )
	#ida_analyzer.PrintFunctionRelationship( 0x40e944, 'dot', 'png' )
	#ida_analyzer.PrintFunctionRelationship( 0x407711, 'dot', 'png' )
	
