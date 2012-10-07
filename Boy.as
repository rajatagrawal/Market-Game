package {

	import Sprites;
	import flash.events.Event;
	import flash.events.KeyboardEvent;
	import flash.ui.Keyboard;
	import fl.transitions.Tween;
	import fl.transitions.easing.*;
	import fl.transitions.TweenEvent;
	import flash.media.Sound;
	import flash.media.SoundChannel;
	import flash.net.URLRequest;

	public class Boy extends Sprites {
		
		public var myTween:Tween;
		private var walkingSound:Sound;
		
		public function Boy(size:Number,left:Number,right:Number,up:Number,down:Number, target:Array) {
			super(size,left,right,up,down);
			this.initial_sprite_dir = "back";
			animals=target;
		}
		
		public function loadSounds():void {
			walkingSound = new Sound(new URLRequest("Audio/walking.mp3"));
		}
		
		public function addListeners():void {
			this.addEventListener(Event.ADDED_TO_STAGE, enteredFrame);
		}
		
		public function enteredFrame(e:Event):void {
			stage.addEventListener(KeyboardEvent.KEY_DOWN,moveBoy);
			removeEventListener(Event.ADDED_TO_STAGE, enteredFrame);
		}
		
		public function moveBoy(e:KeyboardEvent):void {
			
			Market.boyIsMoving = true;
			
			
			if(Market.goNextFrame==false){
				if (e.keyCode == Keyboard.RIGHT) {
					walkingSound.play();
					moveSprite("right",this.moveStepSize);
				} else if (e.keyCode == Keyboard.LEFT) {
					walkingSound.play();
					moveSprite("left",this.moveStepSize);
				} else if (e.keyCode == Keyboard.UP) {
					walkingSound.play();
					moveSprite("up",this.moveStepSize);
				} else if (e.keyCode == Keyboard.DOWN) {
					walkingSound.play();
					moveSprite("down",this.moveStepSize);
				}
			}
			if(this.x>660 && this.y<190)
			{
				Market.boyIsMoving = false;
				this.gotoAndStop("right");
				stage.removeEventListener(KeyboardEvent.KEY_DOWN,moveBoy);
				myTween = new Tween(this, "x", Strong.easeOut, this.x, 800, 4, true);
				myTween.addEventListener(TweenEvent.MOTION_FINISH, gotoNextFrame);
			}
		}
		
		public function gotoNextFrame(e:Event):void{
			myTween.removeEventListener(TweenEvent.MOTION_FINISH, gotoNextFrame);
			//stage.removeEventListener(KeyboardEvent.KEY_DOWN,moveBoy);
			Market.goNextFrame = true;
		}
		
		
	}
}