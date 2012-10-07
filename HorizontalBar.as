package {
	import flash.display.MovieClip;
	import flash.text.TextField;
	import flash.net.URLRequest;
	import flash.events.Event;
	import flash.events.MouseEvent;
	import flash.display.Loader;
	import flash.text.TextField;
	import flash.text.TextFormat;
	
	public class HorizontalBar extends MovieClip
	{
		public var horizontalBar:ImageToMovie;
		public var buttonTextLeft:TextField;
		public var buttonTextRight:TextField;
		public var textStyling:TextFormat;
		public var repeat:MovieClip;
		public var nextWord:MovieClip;
		
		public function HorizontalBar()
		{
			repeat = new MovieClip();
			nextWord = new MovieClip();
			horizontalBar = new ImageToMovie("Images/horizontalBar.jpg");
			horizontalBar.setX(0);
			horizontalBar.setY(453);
			horizontalBar.scaleX = 1.61;
			buttonTextLeft = new TextField();
			buttonTextRight = new TextField();
			textStyling = new TextFormat();
			textStyling.size = 24;
			textStyling.color = 0xFFFFFF;
			buttonTextLeft.setTextFormat(textStyling);
			buttonTextRight.setTextFormat(textStyling);
			addChild(horizontalBar);
			addChild(repeat);
			addChild(nextWord);
			
			repeat.addChild(buttonTextLeft);
			repeat.x = 20;
			repeat.y = 450;
			nextWord.addChild(buttonTextRight);
			nextWord.x = 700;
			nextWord.y = 450;
		}
		
		public function leftSoftKey(text:String) {
			buttonTextLeft.text = text;
		}
		
		public function rightSoftKey(text:String) {
			buttonTextRight.text = text;
		}
		
		public function bar_invisible():void {
			horizontalBar.hideImage();
			repeat.visible = false;
			nextWord.visible = false;
		}
		
		public function bar_visible():void {
			horizontalBar.showImage();
			repeat.visible = true;
			nextWord.visible = true;
		}
	}
}