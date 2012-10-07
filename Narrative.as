﻿package {	import flash.display.MovieClip;	import flash.net.URLRequest;	import flash.media.*;	import flash.events.Event;	import flash.events.MouseEvent;	import flash.events.KeyboardEvent;	import flash.ui.Keyboard;	import flash.display.Loader;	import flash.text.TextField;	import flash.text.TextFormat;	import flash.text.TextFieldAutoSize;	import flash.utils.*;	import fl.transitions.easing.*;	import fl.transitions.Blinds;	import fl.transitions.TransitionManager;	import fl.transitions.Transition;	import fl.transitions.Tween;	import fl.transitions.TweenEvent;		public class Narrative extends MovieClip 	{		private var counter:Number;		private var dialogueSound:Array;		private var dialoguesArray:Array;		private var syllabusArray:Array;		public var movieFinished:Boolean;		private var soundFinished:Boolean;		private var soundChannel_1:SoundChannel;		private var soundChannel_1_telegu:SoundChannel;		private var repeatFlag:Boolean;		// this variable will be used to store the images		private var imageLoader:Array;		// this variable will be used to store the audio associated with the images		private var soundFiles:Array;		private var soundFiles_telegu:Array;				// this is the button to repeat the animation for a syllabus word		private var repeat:MovieClip;				// this is the button to move to the next word		private var nextWord:MovieClip;				// this stores the text to be displayed on the button		private var buttonText1:TextField;		private var buttonText2:TextField;		private var buttonText1_telegu:TextField;		private var buttonText2_telegu:TextField;		private var textStyling:TextFormat;		private var textStyling_telegu_1:TextFormat;				private var horizontalBar:ImageToMovie;				// this variable will keep a track of the image being displayed		private var imageTracker:int				// used to store the return value of setInterval		// setInterval will be used to put a delay of 1 sec		// the delay is used for the gap between displaying image of a word		// the L2 word spoken		private var delay:uint;		var myTransitionManager:TransitionManager;		private var syllabusTween:Tween;		private var imageNumber_1:int;				private var motherBubbleTween:Tween;		private var sonBubbleTween:Tween;				private var motherBubbleTween2:Tween;		private var sonBubbleTween2:Tween;				private var channel_bubble:SoundChannel;		private var textField_telegu:Array;		private var textStyling_telegu:TextFormat;		private var fileCopystageBackground:MovieClip;		private var dialogueTextField_mother:TextField;		private var dialogueTextField_raju:TextField;		private var dialogueStyling:TextFormat;		private var errorTextField:TextField;				private var speakNow:Sound;		private var speakNow_soundChannel:SoundChannel;				private var compareString:String;		private var imageFilenames:Array;		private var correct:MovieClip;		private var time:Date;		private var microphoneImageLoader:Loader;		private var englishText:String;		private var englishTextStyling:TextFormat;		private var englishTextArray:Array;				private var disappearTeleguText:Tween;		private var disappearEnglishText:Tween;		private var gujaratiFontVariable:gujaratiFont;		public function Narrative(dialogues:Array, syllabus:Array,stageBackground:MovieClip)		{			try{							correct = new Correct();			correct.visible = false;			setupEnglishText();			dialogueSound = new Array(dialogues.length);			syllabusArray = new Array(syllabus.length);			speakNow = new Sound(new URLRequest("Audio/speakNow_telegu.mp3"));			speakNow_soundChannel = new SoundChannel();			compareString = new String();			gujaratiFontVariable = new gujaratiFont();					imageFilenames = new Array();			errorTextField = new TextField();			addChild(errorTextField);			errorTextField.visible = false;			errorTextField.x = 400;			errorTextField.y = 200;			errorTextField.width = 1000;			fileCopystageBackground = stageBackground;			initialiseTheTeleguTextField();			channel_bubble = new SoundChannel();			motherBubbleTween = new Tween(Market.mother_bubble,"alpha",Regular.easeIn,0,1,0.5,true);			motherBubbleTween.stop();			sonBubbleTween = new Tween(Market.son_bubble,"alpha",Regular.easeIn,0,1,0.5,true);			sonBubbleTween.stop();			motherBubbleTween2 = new Tween(Market.mother_bubble,"alpha",Regular.easeIn,1,0,0.5,true);			motherBubbleTween2.stop();			sonBubbleTween2 = new Tween(Market.son_bubble,"alpha",Regular.easeIn,1,0,0.5,true);			sonBubbleTween2.stop();			setupTheButtons();			addEventListener(Event.ADDED_TO_STAGE,startKeyboardListener);			dialoguesArray = dialogues;			syllabusArray = syllabus;			movieFinished = false;			counter = 0;			imageTracker =0;			soundFinished = true;			soundChannel_1 = new SoundChannel();			soundChannel_1_telegu = new SoundChannel();						loadDialogues();						// initiliazing the size of this array to 5			imageLoader = new Array();			soundFiles = new Array();			soundFiles_telegu = new Array();			loadImages(Market.syllabus);			setupMicrophoneImage();			repeatFlag = false;			addChild(correct);			}			catch(e:Error)			{				errorTextField.text = "an error occured _123" + e.message;			}		}				private function setupMicrophoneImage():void		{			microphoneImageLoader = new Loader();			microphoneImageLoader.load(new URLRequest("Images/rajuMike.png"));			addChild(microphoneImageLoader);			microphoneImageLoader.visible = false;			microphoneImageLoader.x = 0;			microphoneImageLoader.y = 290;					}		private function setupDialogueTextFields():void		{			dialogueStyling = new TextFormat();			dialogueTextField_mother = new TextField();			dialogueTextField_raju = new TextField();			Market.mother_bubble.addChild(dialogueTextField_mother);			Market.son_bubble.addChild(dialogueTextField_raju);						dialogueTextField_mother.wordWrap = true;			dialogueTextField_raju.wordWrap = true;			//dialogueTextField_mother.multiline = true;			//dialogueTextField_raju.multiline = true;						//dialogueTextField_mother.autoSize = TextFieldAutoSize.LEFT;			dialogueTextField_raju.autoSize = TextFieldAutoSize.LEFT;			dialogueTextField_mother.width = 230;			dialogueTextField_raju.width = 200;						dialogueTextField_mother.x = -30;			dialogueTextField_mother.y = -10;						dialogueTextField_raju.y = -10;			dialogueStyling.font = gujaratiFontVariable.fontName;			dialogueStyling.size = 20;			dialogueStyling.bold = true;			dialogueTextField_mother.setTextFormat(dialogueStyling);			dialogueTextField_raju.setTextFormat(dialogueStyling);					}		private function setupEnglishText():void		{			englishText = new String();			englishTextStyling = new TextFormat();						englishTextArray = new Array();									englishTextStyling.size = 32;			englishTextStyling.bold = true;			englishTextStyling.font = "Times New Roman";			englishTextStyling.color = 0x000000;					}		private function startKeyboardListener(e:Event):void		{			stage.addEventListener(KeyboardEvent.KEY_DOWN, myKeyboardListener);			removeEventListener(Event.ADDED_TO_STAGE,startKeyboardListener);		}		private function initialiseTheTeleguTextField():void		{			textField_telegu = new Array();			//addChild(textField_telegu);			//textField_telegu.visible = false;						textStyling_telegu = new TextFormat();			textStyling_telegu.bold = true;			textStyling_telegu.size = 32;			textStyling_telegu.color = 0x000000;			textStyling_telegu.font = gujaratiFontVariable.fontName;			setupDialogueTextFields();												//textField_telegu.setTextFormat(textStyling_telegu);		}				// This function displays a particular image from the array of the images		// stored in imageLoader at index imageNumber		// also displays name of the image in L1		// and plays the sound in L2 after a delay of 1 sec		private function showTheImage(imageNumber:int)		{			soundFinished = false;			correct.visible = false;			fileCopystageBackground.alpha = 0.5;			if (imageNumber != 0)			{				textField_telegu[imageNumber-1].visible = false;				imageLoader[imageNumber -1 ].visible = false;				englishTextArray[imageNumber-1].visible = false;			}			imageNumber_1 = imageNumber;			imageLoader[imageNumber].showImage();						disappearTeleguText = new Tween(textField_telegu[imageNumber],"alpha",Regular.easeIn,0,1,0.5,true);			disappearTeleguText.start();						disappearEnglishText = new Tween(englishTextArray[imageNumber],"alpha",Regular.easeIn,0,1,0.5,true);			disappearEnglishText.start();			textField_telegu[imageNumber].visible = true;			englishTextArray[imageNumber].visible = true;			 			syllabusTween = new Tween(imageLoader[imageNumber],"alpha",Regular.easeIn,0,1,0.5,true);			syllabusTween.start();			syllabusTween.addEventListener(TweenEvent.MOTION_FINISH,playTheSound);		}				private function makeDisappearCurrentImageForPreviousImage(index:int)		{			soundFinished = false;			var disappearTween:Tween;			disappearTween = new Tween(imageLoader[index],"alpha",Regular.easeIn,1,0,0.5,true);			disappearTween.start();			disappearTween.addEventListener(TweenEvent.MOTION_FINISH,showPreviousImage);		}				private function makeImageDisappear(index:int)		{			soundFinished = false;			var disappearTween:Tween;			disappearTween = new Tween(imageLoader[index],"alpha",Regular.easeIn,1,0,0.5,true);			disappearTween.start();						//disappearTeleguText = new Tween(textField_telegu[index],"alpha",Regular.easeIn,1,0,0.5,true);			//disappearTeleguText.start();						//disappearEnglishText = new Tween(englishTextArray[index],"alpha",Regular.easeIn,1,0,0.5,true);			//disappearEnglishText.start();			//textField_telegu[index].visible = false;			//englishTextArray[index].visible = false;			disappearTween.addEventListener(TweenEvent.MOTION_FINISH,imageDisappearFinished);		}				// This function plays the sound stored in the variable soundFiles at		// the index soundNumber		private function playTheSound(e:Event):void		{						//if (soundFinished == true){								soundFinished = false;												soundChannel_1_telegu = soundFiles_telegu[imageNumber_1].play();				soundChannel_1_telegu.addEventListener(Event.SOUND_COMPLETE,playTheTeleguVoiceoverNow);							//}		}		private function playTheTeleguVoiceoverNow(e:Event):void		{						soundChannel_1 = soundFiles[imageNumber_1].play();			soundChannel_1.addEventListener(Event.SOUND_COMPLETE,soundIsComplete);					}				private function soundIsComplete(e:Event):void		{			soundFinished = true;			repeatFlag = true;			//speakNow_soundChannel = speakNow.play();			//speakNow_soundChannel.addEventListener(Event.SOUND_COMPLETE,startTheRecognizer);					}				private function startTheRecognizer(e:Event):void		{			repeatFlag = true;			microphoneImageLoader.visible = true;			Market.sock.addEventListener(SockConnection.DATA_CHANGED, checkAnswer);		}				public function checkAnswer(event:Event):void 		{			repeatFlag = false;			Market.sock.removeEventListener(SockConnection.DATA_CHANGED, checkAnswer);			microphoneImageLoader.visible = false;			compareString = Market.sock._data[0];			compareString = compareString.toLowerCase();			compareString = compareString + ".png";						time = new Date();			echoLog(time.getDate()+ "/" + time.getMonth()+ "/" + time.getFullYear()+ ", "+time.getHours()+"/"+time.getMinutes()+"/"+time.getSeconds()+"/"+time.getMilliseconds()+ ", Teaching, " + imageFilenames[imageNumber_1] + ", " + compareString + ", ");						//Market.sock.sendData("pause\n");			if(imageFilenames[imageNumber_1] == compareString)			{				congratulations();			}			else			{				tryAgain();			}		}		public function echoLog(str:String)		{			Market.sock.sendData("echo \'"+str+"\' >> log.txt");		}		private function congratulations():void		{			correct.visible = true;			correct.x = imageLoader[imageNumber_1].getX() + 37.5;			correct.y = imageLoader[imageNumber_1].getY() + 37.5;			soundFinished = true;		}		private function tryAgain():void		{						playTheSound(null);		}		private function setupTheButtons():void		{			repeat = new MovieClip();			nextWord = new MovieClip();			horizontalBar = new ImageToMovie("Images/horizontalBar.jpg");						addChild(horizontalBar);			addChild(repeat);			addChild(nextWord);						repeat.visible = false;			nextWord.visible = false;			horizontalBar.hideImage();		}		private function initialiseTheButtons():void		{									horizontalBar.setX(0);			horizontalBar.setY(453);			horizontalBar.scaleX = 1.61;						buttonText1 = new TextField();			buttonText2 = new TextField();			buttonText1_telegu = new TextField();			buttonText2_telegu = new TextField();			textStyling = new TextFormat();			buttonText1.text = "Repeat";			buttonText2.text = "Next";			buttonText1_telegu.text = "ફરી થી"; // telegu version for "repeat"			buttonText2_telegu.text = "આગલો"; // telegu version for "next"									textStyling.size = 24;			textStyling.color = 0xFFFFFF;			buttonText1.autoSize = TextFieldAutoSize.LEFT;			buttonText2.autoSize = TextFieldAutoSize.LEFT;			buttonText1.setTextFormat(textStyling);			buttonText2.setTextFormat(textStyling);						textStyling_telegu_1 = new TextFormat();			textStyling_telegu_1.color = 0xFFFFFF;			textStyling_telegu_1.size = 24;			textStyling_telegu_1.font =gujaratiFontVariable.fontName;						buttonText1_telegu.setTextFormat(textStyling_telegu_1);			buttonText2_telegu.setTextFormat(textStyling_telegu_1);						buttonText1_telegu.x = buttonText1.width + 10;			buttonText2_telegu.x = buttonText2.width + 10;			buttonText1_telegu.y = 4;			buttonText2_telegu.y = 4;			buttonText1_telegu.width = 350;			buttonText2_telegu.width = 350;						horizontalBar.showImage();			repeat.visible = true;			nextWord.visible = true;			repeat.addChild(buttonText1);			repeat.addChild(buttonText1_telegu);						repeat.x = 20;			repeat.y = 450;			nextWord.addChild(buttonText2);			nextWord.addChild(buttonText2_telegu);						nextWord.x = 600;			nextWord.y = 450;			//nextWord.addEventListener(MouseEvent.CLICK, showNextImage);			//repeat.addEventListener(MouseEvent.CLICK, repeatTheImage);		}				private function myKeyboardListener(e:KeyboardEvent):void		{			errorTextField.text = " a key is being pressed ";			if (repeat.visible == true)			{				if (e.keyCode == 81) // key code for q				//if (e.keyCode == Keyboard.SPACE)				{					//if (soundFinished == true)					if(repeatFlag==true)					{						imageNumber_1 = imageTracker;						repeatTheImage();					}				}								else if (e.keyCode == 80 || e.keyCode == Keyboard.RIGHT) // key code for p				//else if (e.keyCode == Keyboard.ENTER)				{					if (soundFinished == true)						makeImageDisappear(imageTracker);						//showNextImage();									}								else if (e.keyCode == Keyboard.LEFT)				{					if (soundFinished == true)					{						if (imageTracker>0)						{							makeDisappearCurrentImageForPreviousImage(imageTracker);						}					}				}			}		}				private function imageDisappearFinished(e:TweenEvent)		{			showNextImage();		}		private function showPreviousImage(e:TweenEvent)		{						imageTracker = imageTracker - 1;			repeatFlag = false;						if (imageTracker >=0)			{				soundFinished = false;				correct.visible = false;				fileCopystageBackground.alpha = 0.5;									textField_telegu[imageTracker+1].visible = false;					//imageLoader[imageTracker +1 ].visible = false;					englishTextArray[imageTracker+1].visible = false;								imageNumber_1 = imageTracker;				imageLoader[imageTracker].showImage();				imageLoader[imageTracker].visible = true;				textField_telegu[imageTracker].visible = true;				englishTextArray[imageTracker].visible = true;				syllabusTween = new Tween(imageLoader[imageTracker],"alpha",Regular.easeIn,0,1,0.5,true);				syllabusTween.start();				//disappearTeleguText = new Tween(textField_telegu[imageTracker],"alpha",Regular.easeIn,0,1,0.5,true);				//disappearTeleguText.start();				syllabusTween.addEventListener(TweenEvent.MOTION_FINISH,playTheSound);				}		}		private function showNextImage():void		{			imageTracker = imageTracker + 1;			repeatFlag = false;						if (imageTracker == 5)			{				stage.removeEventListener(KeyboardEvent.KEY_DOWN, myKeyboardListener);				movieFinished = true;				repeat.visible = false;				nextWord.visible = false;				removeChild(horizontalBar)				imageLoader[4].visible = false;				//nextWord.removeEventListener(MouseEvent.CLICK, showNextImage);				//repeat.removeEventListener(MouseEvent.CLICK, repeatTheImage);								return;			}			showTheImage(imageTracker);							}				private function repeatTheImage():void {			if (repeatFlag == true)			{				microphoneImageLoader.visible = false;				repeatFlag = false;				//showTheImage(imageTracker);				playTheSound(null);			}		}						// this function loads the images which need to be taught 		// to the child in the variable imageLoader		// this function also loads the sounds corresponding to those images in the variable soundFiles		// parameters 		// 1. list : this is the array which stores the words which need to be taught		private function loadImages(list:Array)		{			// this variable is used to traverse the variable "list"			var counter_1:Number = 0;			while(counter_1<list.length)			{				// store the images in the imageLoader array														imageLoader.push(new ImageToMovie("Images/" + list[counter_1].image));				imageFilenames.push(new String(list[counter_1].image));				textField_telegu.push(new TextField());				addChild(textField_telegu[counter_1]);				textField_telegu[counter_1].visible = false;				textField_telegu[counter_1].x = 85;				textField_telegu[counter_1].y = 100;				textField_telegu[counter_1].autoSize = TextFieldAutoSize.CENTER;				textField_telegu[counter_1].text = list[counter_1].transliteration;				textField_telegu[counter_1].setTextFormat(textStyling_telegu);								englishTextArray.push(new TextField());				addChild(englishTextArray[counter_1]);				englishTextArray[counter_1].visible = false;				englishText = list[counter_1].image;				englishText = englishText.toUpperCase();				englishText = englishText.substr(0,englishText.length - 4);				englishTextArray[counter_1].text = englishText;				englishTextArray[counter_1].autoSize = TextFieldAutoSize.CENTER;				englishTextArray[counter_1].y = 70;				englishTextArray[counter_1].x = 125;				englishTextArray[counter_1].setTextFormat(englishTextStyling);								soundFiles.push(new Sound());				soundFiles[counter_1].load(new URLRequest("Audio/" + list[counter_1].audio));				soundFiles_telegu.push(new Sound());				soundFiles_telegu[counter_1].load(new URLRequest("Audio/" + list[counter_1].name + "_telegu.mp3"));								this.addChild(imageLoader[counter_1]);								// hide the images				//imageLoader[counter_1].visible = false;				imageLoader[counter_1].hideImage();				// bring the images to the bottom left corner of the screen.				imageLoader[counter_1].setX(40);				imageLoader[counter_1].setY(140);								// shrink the size of the images by half								imageLoader[counter_1].scaleX = 1;				imageLoader[counter_1].scaleY= 1;												counter_1 = counter_1 + 1;			}		}						//Load the audio files for dialogues		private function loadDialogues():void		{			var i:int=0;			for(i=0;i<dialoguesArray.length;i++)			{				dialogueSound[i] = new Sound(new URLRequest("Audio/"+dialoguesArray[i].audio));			}			dialogueSound[i-1].addEventListener(Event.COMPLETE, playDialogues);		}		private function motherDialogueStarted(e:Event):void		{			channel_bubble = dialogueSound[counter].play();			counter++;			channel_bubble.addEventListener(Event.SOUND_COMPLETE, playDialogues);		}		private function sonDialogueFinished(e:Event):void		{			//Market.mother_bubble.mother_speech.text=dialoguesArray[counter].text;			Market.son_bubble.son_speech.text="";			Market.mother_bubble.visible=true;			dialogueTextField_mother.text = dialoguesArray[counter].text;			dialogueTextField_mother.setTextFormat(dialogueStyling);						motherBubbleTween.start();			motherBubbleTween.addEventListener(TweenEvent.MOTION_FINISH,motherDialogueStarted);			Market.son_bubble.visible=false;		}		private function motherDialogueFinished(e:Event):void		{			Market.son_bubble.visible = true;			//Market.son_bubble.son_speech.text=dialoguesArray[counter].text;			dialogueTextField_raju.text = dialoguesArray[counter].text;			dialogueTextField_raju.setTextFormat(dialogueStyling);			Market.mother_bubble.mother_speech.text="";			Market.mother_bubble.visible=false;			sonBubbleTween.start();			sonBubbleTween.addEventListener(TweenEvent.MOTION_FINISH,motherDialogueStarted);						}		private function playDialogues(soundEvent:Event):void		{			//var channel:SoundChannel = new SoundChannel();			if(counter<dialoguesArray.length)			{				if(dialoguesArray[counter].speaker=="Mother")				{					sonBubbleTween2.start();					sonBubbleTween2.addEventListener(TweenEvent.MOTION_FINISH,sonDialogueFinished);																							}							else if(dialoguesArray[counter].speaker=="Raju")				{					motherBubbleTween2.start();					motherBubbleTween2.addEventListener(TweenEvent.MOTION_FINISH,motherDialogueFinished);														}			}			else			{				Market.mother_bubble.visible=false;				Market.son_bubble.visible=false;				dialogueTextField_raju.text = "";				dialogueTextField_raju.setTextFormat(dialogueStyling);				dialogueTextField_mother.text = "";				dialogueTextField_mother.setTextFormat(dialogueStyling);				initialiseTheButtons();				showTheImage(imageTracker);				return;			}		}	}}