package {
 	import flash.display.MovieClip;
	import flash.text.TextField;
 
 	public class Market extends MovieClip
 	{
  		public static var mother_bubble:MovieClip = new Mother_bubble();
		public static var son_bubble:MovieClip = new Son_bubble();
		public static var questionNumber:Number;
		public static var boyIsHit:Boolean;
		public static var boyIsMoving:Boolean;
		public static var goNextFrame:Boolean;
		public static var enterPressed:Boolean;
		public static var syllabus:Array;
		public static var gameLevelNo:int;
		public static var sock:SockConnection;
  
  		public function Market()
  		{
   			this.stage.addChild(mother_bubble);
			this.stage.addChild(son_bubble);
   			mother_bubble.y=35; mother_bubble.x=175;
			son_bubble.y=65; son_bubble.x=585;
			mother_bubble.visible=false;
			son_bubble.visible=false;
			syllabus = new Array(5);
			questionNumber = 1;
			gameLevelNo = 1;
			boyIsHit = false;
			enterPressed = false;
			boyIsMoving = false;
			goNextFrame = false;
			sock=new SockConnection("localhost",5000);  
			//sock.sendData("start");
  		}
		
		public static function populateSyllabus():void {
			syllabus = SyllabusQueue.nextWords(5); //5 words extracted from the word queue each round
		}
 	}
}