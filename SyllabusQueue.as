package{

	public class SyllabusQueue {
		
		public static var syllabusArray:Array;

		public function SyllabusQueue():void {
			syllabusArray=new Array();
		}

		public function addSyllabusItem(name:String,audio:String,image:String, d_phone:String, d_semantic:String, d_unrelated:String,d_transliteration:String):void {
			var tempSyllabusItem:SyllabusItem=new SyllabusItem(name,audio,image, d_phone, d_semantic, d_unrelated, d_transliteration,1);
			syllabusArray.push(tempSyllabusItem);
		}

		public static function nextWords(numberOfWords:int):Array{
			var i:int;
			var syllabusWords:Array = new Array();
			for(i=0;i<numberOfWords;i++)
			{
				syllabusWords.push(syllabusArray[i]);
			}
			return syllabusWords;
		}
		
		public static function updateWordWeight(word:String,weight:int):void{
			var i:int;
			for (i=0;i<syllabusArray.length;i++)
			{
				if(word==syllabusArray[i].name)
				{
					syllabusArray[i].weight = syllabusArray[i].weight + weight;
					break;
				}
			}
		}
		
		public static function updateSyllabusQueue():void{
			syllabusArray.sortOn("weight");
		}
		
	}
}