from autosar.writer.writer_base import BaseWriter
from autosar.writer.package_writer import PackageWriter
from autosar.base import applyFilter
import collections

class WorkspaceWriter(BaseWriter):
   def __init__(self, version, patch, schema, packageWriter):
      super().__init__(version, patch)
      assert(isinstance(packageWriter, PackageWriter))
      self.schema = schema
      self.packageWriter=packageWriter
      
   def beginFile(self):
      lines=[]      
      if (self.version >= 3.0) and (self.version < 4.0):
         lines.append('<?xml version="1.0" encoding="UTF-8"?>')
         versionString = "%d.%d.%d"%(self.major, self.minor, self.patch)
         if self.schema is None:
            schema = 'autosar_'+versionString+'.xsd'
         else:
            schema = self.schema
         lines.append('<AUTOSAR xsi:schemaLocation="http://autosar.org/%s %s" xmlns="http://autosar.org/%s" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'%(versionString, schema, versionString))
         lines.append(self.indentChar+'<TOP-LEVEL-PACKAGES>')
      elif self.version >= 4.0:         
         lines.append('<?xml version="1.0" encoding="utf-8"?>')
         lines.append('<AUTOSAR xsi:schemaLocation="http://autosar.org/schema/r4.0 AUTOSAR_{0}-{1}-{2}.xsd" xmlns="http://autosar.org/schema/r4.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'.format(self.major, self.minor, self.patch))
         lines.append(self.indentChar+'<AR-PACKAGES>')
      return lines
   
   def endFile(self):
      lines=[]
      if (self.version >= 3.0) and (self.version<4.0):
         lines.append(self.indentChar+'</TOP-LEVEL-PACKAGES>')
      else:
         lines.append(self.indentChar+'</AR-PACKAGES>')
      lines.append('</AUTOSAR>')
      return lines

   
   def saveXML(self, ws, fp, filters):
      fp.write(self.toXML(ws, filters))

   def toXML(self, ws, filters):
      lines=self.beginFile()
      result='\n'.join(lines)+'\n'
      for package in ws.packages:
         if applyFilter(package.ref, filters):
            lines=self.packageWriter.toXML(package, filters)
            if len(lines)>0:
               lines=self.indent(lines,2)
               result+='\n'.join(lines)+'\n'
      lines=self.endFile()
      return result+'\n'.join(lines)+'\n'
   
   def toCode(self, ws, packages=None, ignore=None, head=None, tail=None, module=False, indent=3):
      localvars = collections.OrderedDict()
      localvars['ws']=ws
      indentStr=indent*' '
      if module == False:
         #head
         if head is None:
            lines=['import autosar', 'ws=autosar.workspace()']
            result='\n'.join(lines)+'\n\n'
         else:            
            if isinstance(head,list):
               head = '\n'.join(head)
            assert(isinstance(head,str))
            result = head+'\n\n'      
         
         
         #body
         for package in ws.packages:
            if (isinstance(packages, collections.Iterable) and package.name in packages) or (isinstance(packages, str) and package.name==packages) or (packages is None):
               lines=self.packageWriter.toCode(package, ignore, localvars)
               if len(lines)>0:
                  result+='\n'.join(lines)+'\n'
         #tail
         if tail is None:
            result+='\n'+'print(ws.toXML())\n'
         else:
            if isinstance(tail,list):
               tail = '\n'.join(tail)
            assert(isinstance(tail,str))
            result+='\n'+tail
         return result
      else:
         if head is None:
            head=[
               ['import autosar'],
               ['ws = autosar.workspace()']
            ]
         if len(head)!=2:
            raise ValueError('when module=True then head must have exactly two elements (list of lists)')
         if isinstance(head[0], collections.Iterable):
            head[0] = '\n'.join(head[0])
         assert(isinstance(head[0],str))
         result = head[0]+'\n\n'
         #body
         result+='def apply(ws):\n'
         for package in ws.packages:
            if (isinstance(packages, collections.Iterable) and package.name in packages) or (isinstance(packages, str) and package.name==packages) or (packages is None):
               lines=self.packageWriter.toCode(package, ignore, localvars)
               if len(lines)>0:
                  lines=[indentStr+x for x in lines]
                  result+='\n'.join(lines)+'\n'
         
         #tail
         result+="\nif __name__=='__main__':\n"
         if isinstance(head[1], collections.Iterable):
            head[1] = '\n'.join([indentStr+x for x in head[1]])
         else:
            head[1] = '\n'.join([indentStr+x for x in head[1].split('\n')])
         assert(isinstance(head[1],str))
         result+=head[1]+'\n'
         result+=indentStr+'apply(ws)\n'
         if tail is None:
            result+=indentStr+'print(ws.toXML())\n'
         else:
            if isinstance(tail,list):
               tail = '\n'.join([indentStr+x for x in tail])
            else:
               tail = '\n'.join([indentStr+x for x in tail.split('\n')])
            assert(isinstance(tail,str))
            result+=tail+'\n'
         return result
      

      
   def saveCode(self, ws, fp, packages=None, ignore=None, head=None, tail=None, module=False):
      fp.write(self.toCode(ws, packages, ignore, head, tail, module))