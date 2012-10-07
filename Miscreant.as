package
{
	public class Miscreant extends Sprites
	{
		import flash.events.Event;
		import flash.net.URLRequest;
		import flash.media.Sound;
		import flash.media.SoundChannel;
		private var distance:Number;
		private var xDifference:Number;
		private var yDifference:Number;
		private var xSign:Number;
		private var ySign:Number;
		private var hitSound:Sound;
		
		private var hitSoundChannel:SoundChannel;
		
		function Miscreant(size:Number,separation:Number,left:Number,right:Number,up:Number,down:Number)
		{
			distance = separation;
			initial_sprite_dir = "front";
			hitSound = new Sound(new URLRequest("Audio/hit.mp3"));
			hitSoundChannel = new SoundChannel();
			super(size,left,right,up,down);
		}
		
		public function moveTowardsTarget(target:Sprites):void
		{
			xSign = 0;
			ySign = 0;
			xDifference = this.getX() - target.getX();
			yDifference = this.getY()+this.height - (target.getY()+target.height);
			if (xDifference!=0)
				xSign = xDifference/Math.abs(xDifference);
			if (yDifference!=0)
				ySign = yDifference/Math.abs(yDifference);
			
			if (Math.abs(xDifference)<= distance && Math.abs(yDifference) <= distance && Market.boyIsHit==false && Market.boyIsMoving==true)
			{
				var ran:Number = Math.floor(Math.random()*2);
				if (ran == 0) {
					xSign = 0;
				} else {
					ySign = 0;
				}
				
				if(this.moveStepSize < Math.abs(xDifference))
					this.x = this.x - xSign*this.moveStepSize;
				else
					this.x = this.x - xSign*Math.abs(xDifference);
					
				if(this.moveStepSize < Math.abs(yDifference))
					this.y = this.y - ySign*this.moveStepSize;
				else
					this.y = this.y - ySign*Math.abs(yDifference);
				
				if(checkHitTarget()==true)
				{
					Market.boyIsHit = true;
					hitSoundChannel = hitSound.play(0,5);
					target.blink(this);
				}
			}
		}
		
		public function checkHitTarget():Boolean
		{
			if(Math.abs(xDifference)<25 && Math.abs(yDifference)<15)
				return true;
			else
				return false;
		}
	}
}