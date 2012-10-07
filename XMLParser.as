package{
  import flash.xml.*;
  import flash.events.Event;
  import flash.net.*;

  public class XMLParser{
    private var xDoc:XMLDocument;
	public var xmlLoader:URLLoader;
	public var syllabus:SyllabusQueue;
	public static var totalLevels:int;
	public static var wordsPerLevel:int;
	public static var dialogues:Array;
	
	//Loads the new XML file
    public function XMLParser(filename:String){
		dialogues = new Array();
		syllabus = new SyllabusQueue();
		var xmlString:URLRequest = new URLRequest(filename);
		xmlLoader = new URLLoader(xmlString);
		xmlLoader.addEventListener(Event.COMPLETE, init);
    }
	
	//Parses the first level nodes of the XML and passes the control to relevant child nodes handlers
	public function init(event:Event):void{
		var gameXML:XML = XML(xmlLoader.data);
  		xDoc = new XMLDocument();
      	xDoc.ignoreWhite = true;
      	xDoc.parseXML(gameXML.toXMLString());
		var i:int;
		totalLevels = xDoc.firstChild.attributes.levels;
		wordsPerLevel = xDoc.firstChild.attributes.words_per_level;
		for(i=0; i<xDoc.firstChild.childNodes.length; i++)
		{
			if(xDoc.firstChild.childNodes[i].nodeName=="dialogues")
				init_dialogues(i);
			else if(xDoc.firstChild.childNodes[i].nodeName=="curricula")
			{
				init_curricula(i);
			}else
				trace("Incorrect Parsing!");
		}
		SyllabusQueue.updateSyllabusQueue();
	}
	
	//Parses Dialogues child node
	public function init_dialogues(nodeNumber:int):void{
		var i:int;
		for (i=0;i<xDoc.firstChild.childNodes[nodeNumber].childNodes.length;i++)
		{
			var dialogueData = new Object();
			dialogueData.speaker=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.speaker;
			dialogueData.text=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.text;
			dialogueData.audio=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.audio;
			dialogues.push(dialogueData);
		}
	}
	
	//Parses Curricula child node
	public function init_curricula(nodeNumber:int):void{
		var i:int;
		for (i=0;i<xDoc.firstChild.childNodes[nodeNumber].childNodes.length;i++)
		{
			var curriculumData = new Object();
			curriculumData.name=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.name;
			curriculumData.image=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.image;
			curriculumData.audio=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.audio;
			curriculumData.phonological_dist=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.phonological_dist;
			curriculumData.semantic_dist=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.semantic_dist;
			curriculumData.unrelated_dist=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.unrelated_dist;
			curriculumData.transliteration=xDoc.firstChild.childNodes[nodeNumber].childNodes[i].attributes.transliteration;
			syllabus.addSyllabusItem(curriculumData.name, curriculumData.audio, curriculumData.image, curriculumData.phonological_dist, curriculumData.semantic_dist, curriculumData.unrelated_dist,curriculumData.transliteration);
		}
	}
  }
}