package {
	import flash.display.MovieClip;
	import flash.net.URLRequest;
	import flash.display.Loader;

	public class ImageToMovie extends MovieClip {

		private var character:MovieClip;
		private var URLImage:URLRequest;
		private var image:Loader;
		public var rightImage:Boolean;

		public function ImageToMovie(filename:String) {
			URLImage=new URLRequest(filename);
			image=new Loader  ;
			image.load(URLImage);
			rightImage=false;
			character=new MovieClip  ;
			addChild(character);
			character.addChild(image);
			character.visible=false;
		}
		public function getHeight():Number {
			return image.height;
		}
		public function getWidth():Number {
			return image.width;
		}
		public function setHeight(theHeight:Number) {
			image.height=theHeight;
			character.height=theHeight;
		}
		public function setWidth(theWidth:Number) {
			image.width=theWidth;
			character.width=theWidth;
		}
		public function getX():Number {
			return character.x;
		}
		public function getY():Number {
			return character.y;
		}
		public function setX(x:Number):void {
			character.x=x;
		}
		public function setY(y:Number):void {
			character.y=y;
		}
		public function hideImage() {
			character.visible=false;
		}
		public function showImage() {
			character.visible=true;
		}
	}
}