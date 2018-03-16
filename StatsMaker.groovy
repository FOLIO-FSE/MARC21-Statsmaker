@GrabResolver(name = 'jitpack.io', root = 'https://jitpack.io')
@Grapes([
    @Grab('org.codehaus.groovy:groovy-all:2.4.13'),
    @Grab('io.github.http-builder-ng:http-builder-ng-core:1.0.3'),
    @Grab('com.github.libris:jmarctools:bb97de39cb41e7455ecb29af0ed5f27f2e9cc797'),
	@Grab('org.codehaus.jackson:jackson-mapper-asl:1.9.12')

])

import se.kb.libris.util.marc.Controlfield
import se.kb.libris.util.marc.MarcRecord
import se.kb.libris.util.marc.impl.MarcRecordImpl
import se.kb.libris.util.marc.io.Iso2709MarcRecordReader
import se.kb.libris.util.marc.io.MarcXmlRecordReader
import org.codehaus.jackson.map.ObjectMapper
import groovy.io.FileType

import org.codehaus.jackson.map.ObjectMapper
import org.codehaus.jackson.node.ObjectNode
import static groovy.json.JsonOutput.*

def files = getFiles(args[0])

println "Number of Files:\t\t ${files.count{it}}"

files.each{file ->	
	def reader = new Iso2709MarcRecordReader(file)
	MarcRecordImpl record 
	while(record = reader.readRecord()){
		printAllMatchingCriteria("696", {it.tag == '696'}, record)
		printAllMatchingCriteria("697", {it.tag == '697'}, record)
		printAllMatchingCriteria("698", {it.tag == '698'}, record)
		printAllMatchingCriteria("951", {it.tag == '951'}, record)
		printAllMatchingCriteria("951-2-4", {it.tag == '951' && it.getIndicator(1)=='4'}, record)
			
	}
}


void printAllMatchingCriteria(String nameOfCriteria, def closure, def record){
	def fieldsWithTag = record.datafields.findAll{it->closure}                             
	if(fieldsWithTag){                                                                           
        	fieldsWithTag.each{fieldWithTag->                                                               
                	print "$nameOfCriteria\t"                                                       
                	print record.leader
			print "\t"	
			print record.controlfields.find{ it-> it.tag == '001'}?.data         
                	print "\t"     
			print record.controlfields.find{ it-> it.tag == '006'}?.data
                        print "\t"
                        print record.controlfields.find{ it-> it.tag == '007'}?.data
                        print "\t"
                        print record.controlfields.find{ it-> it.tag == '008'}?.data			
			print "\t"
			print fieldWithTag.subfields.find{it->it.code=="a"}?.data                                                     
           		print "\t"
			print fieldWithTag.getIndicator(0)
			print "\t"                	
			print fieldWithTag.getIndicator(1)
			println ""
         	}                                                                           
	}  
}

List<File> getFiles(String folderPath){
	def list = []
	def dir = new File(folderPath)
	dir.eachFileRecurse (FileType.FILES) { file ->
	  list << file
	}
	return list
}
