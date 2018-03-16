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
println args[0]
int numRecords = 0

println "Number of Files:\t ${files.count{it}}"

files.each{file ->	
	println "Name:\t$file.path"
	def reader = new Iso2709MarcRecordReader(file)
	MarcRecordImpl record 
	while(record = reader.readRecord()){
		numRecords++
		
		printAllWithTag(696, {it.tag == '696'}, record, numRecords)
		printAllWithTag(697, {it.tag == '697'}, record, numRecords)
		printAllWithTag(698, {it.tag == '698'}, record, numRecords)
		printAllWithTag(951, {it.tag == '951' && it.getIndicator(1)=='4'}, record, numRecords)
			
	}
}


void printAllWithTag(int tag, def closure, def record, int numRecords){
	def fieldsWithTag = record.datafields.findAll{it->it.tag=="$tag"}                             
	if(fieldsWithTag){                                                                           
        	fieldsWithTag.each{fieldWithTag->                                                               
                	print "$tag\t"                                                       
                	print record.leader
			print "\t"	
			print record.controlfields.find{ it-> it.tag == '001'}.data         
                	print "\t"     
			print record.controlfields.find{ it-> it.tag == '006'}?.data
                        print "\t"
                        print record.controlfields.find{ it-> it.tag == '007'}?.data
                        print "\t"
                        print record.controlfields.find{ it-> it.tag == '008'}?.data			
			print "\t"
			print  prettyPrint(toJson(fieldWithTag.subfields.find{it->it.code=="a"}.data))                                                     
           		print "\t"
			print toJson(fieldWithTag.getIndicator(0))
			print "\t"                	
			print toJson(fieldWithTag.getIndicator(1))
			println "\t$numRecords"
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

ObjectNode toObjectNode(MarcRecordImpl record) {
	ObjectMapper mapper = new ObjectMapper()        
	def json = mapper.createObjectNode()
        def fields = mapper.createArrayNode()
        record.fields.each {
            def field = mapper.createObjectNode()
            if (it instanceof Controlfield) {
                field.put(it.tag, it.data)
            } else {
                def datafield = mapper.createObjectNode()
                datafield.put("ind1", "" + it.getIndicator(0))
                datafield.put("ind2", "" + it.getIndicator(1))
                def subfields = mapper.createArrayNode()
                it.subfields.each {
                    def subfield = mapper.createObjectNode()
                    subfield.put(Character.toString(it.code), it.data) //normalizeString(it.data))
                    subfields.add(subfield)
                }
                datafield.put("subfields", subfields)
                field.put(it.tag, datafield)
            }
            fields.add(field)
        }
        json.put("leader", record.leader)
        json.put("fields", fields)
        return json
}

Map toJsonMap(MarcRecordImpl record) {
	ObjectMapper mapper = new ObjectMapper()        
	def node = toObjectNode(record)
        return mapper.readValue(node, Map)
}

String toJSONString(MarcRecordImpl record) {
        return toObjectNode(record).toString()
}
