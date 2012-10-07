package{
	
	public class SyllabusItem {
		public var name:String;
		public var image:String;
		public var weight:int;
		public var audio:String;
		public var phonological_dist: String;
		public var semantic_dist:String;
		public var unrelated_dist:String;
		public var transliteration:String;

		public function SyllabusItem(name:String,audio:String,image:String, phone:String, semantic:String, unrelated:String, transliteration_1:String, weight:int) {
			this.name=name;
			this.audio=audio;
			this.image=image;
			this.phonological_dist = phone;
			this.semantic_dist = semantic;
			this.unrelated_dist = unrelated;
			this.transliteration = transliteration_1;
			this.weight=weight;
		}
	}
}