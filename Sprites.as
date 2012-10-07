package {
	
	import flash.display.MovieClip;
	import flash.net.URLRequest;
	import flash.display.Loader;
	import flash.utils.Timer;
	import flash.events.TimerEvent;
	
	public class Sprites extends MovieClip{

		private var delay:Timer;
		private var blink_counter:int;
		public var moveStepSize:Number;
		public var constraint_right:int;
		public var constraint_left:int;
		public var constraint_up:int;
		public var constraint_down:int;
		public var initial_x:int;
		public var initial_y:int;
		public var initial_sprite_dir:String;
		public var animals:Array;
		
		public function Sprites(size:Number, left:Number,right:Number,up:Number,down:Number) {
			moveStepSize = size;		
			constraint_left = left;
			constraint_right = right;
			constraint_up = up;
			constraint_down = down;
			stop();
		}
		
		public function moveSprite(dir:String, speed:Number):void
		{
			if(Market.boyIsHit == false)
			{
				if(dir=="right"){
					gotoAndStop("right");
					if(x+speed<constraint_right)
						x = x + speed;
				}
				else if(dir=="left"){
					gotoAndStop("left");
					if (x-speed>constraint_left)
						x = x - speed;
				}	
				else if (dir=="up"){
					gotoAndStop("back");
					if(y-speed>constraint_up)
						y = y - speed;
				}
				else if (dir =="down"){
					gotoAndStop("front");
					if (y+speed<constraint_down)
						y = y + speed;
				}
			}
		}
		
		public function getX():Number{
			return this.x;
		}
		
		public function getY():Number{
			return this.y;
		}
		
		public function setX(x:Number):void{
			if (x>= constraint_left && x<=constraint_right)
				this.x = x;
			
			else if (x<constraint_left)
				this.x = constraint_left;
			
			else if (x>constraint_right)
				this.x = constraint_right;
				
			initial_x = this.x;
		}
		
		public function setY(y:Number):void{
			if (y<= constraint_down && y>=constraint_up)
				this.y = y;
			
			else if (y>constraint_down)
				this.y = constraint_down;
			
			else if (y<constraint_up)
				this.y = constraint_up;
				
			initial_y=this.y;
		}
		
		public function restart():void {
			this.x=initial_x;
			this.y=initial_y;
			this.gotoAndStop(initial_sprite_dir);
		}
		
		public function blink(enemy:Sprites):void {
			Market.boyIsMoving = false;
			blink_counter=1;
			delay = new Timer(90,20);
			delay.addEventListener("timer",blink_sprite);
			delay.start();
		}
		
		private function blink_sprite(e:TimerEvent):void
		{
			if (blink_counter%2==1)
				this.alpha = 0;
			
			else if (blink_counter%2 == 0)
				this.alpha = 1;
				
			if (blink_counter%10 == 0)
			{
				restart();
				var i:int;
				for(i=0;i<animals.length;i++)
					animals[i].restart();
			}
			
			if(blink_counter%20 == 0)
			{
				delay.stop();
				Market.boyIsHit=false;
				delay.removeEventListener("timer",blink_sprite);
			}
			
			blink_counter++;
		}
		
	}
	
}
