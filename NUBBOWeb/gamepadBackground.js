// global variables
var gamepads;
var selPad = -1;
var gamePadMode = -1;
var listOfPadVals = [];

var CalibrationOrder = [
    "Dpad-up",
    "Dpad-down",
    "Dpad-left",
    "Dpad-right",
    "Triangle",
    "X",
    "Square",
    "Circle",
    "Start",
    "Select",    
    "Left Hat (L3)",
    "Right Hat (R3)", 
    "L1",
    "R1", 
    "L2",
    "R2", 
    "Left Joystick - up",
    "Left Joystick - down",
    "Left Joystick - left",
    "Left Joystick - right",  
    "Right Joystick - up",
    "Right Joystick - down",
    "Right Joystick - left",
    "Right Joystick - right", 
  ]; 
  var buttonMapping = [];
  var axesMapping = [];
// events
window.addEventListener("gamepadconnected", (event) => {
    window.addEventListener("gamepadconnected", function(e) {
        console.log("Gamepad connected at index %d: %s. %d buttons, %d axes.",
          e.gamepad.index, e.gamepad.id,
          e.gamepad.buttons.length, e.gamepad.axes.length);
      });
  });
  
  window.addEventListener("gamepaddisconnected", (event) => {
    console.log("A gamepad disconnected:");
    console.log(event.gamepad);
  });

  var form = $("#CalibrateButton").on("click", function(e) {
    e.preventDefault();
    console.log("pressed")
    // if controller uncalibrated
    if(gamePadMode  < 0){
        gamePadMode = 0; // set to start calibration mode
        // clear calibration arrays
        buttonMapping = [];
        axesMapping = [];
    }
  });


//   timer to update gamepad states
  var last_selPad = 0;
  var last_gamePadMode = -1;
  var myVar = setInterval(gamepadReaderLoop, 100);
  function gamepadReaderLoop() {
    // try {
        gamepads = navigator.getGamepads();
        // if no gamepad has been selected
        if(selPad == -1){
            selPad = FindActiveGamepad(gamepads);
        }else{ // gamepad selected
            if(gamePadMode >= 0){// ready to calibrate 
               // update the html
               var CalStateStr = "press "+String(CalibrationOrder[gamePadMode]);
               document.getElementById("CalibrationState").innerHTML = CalStateStr;
               //detect button presses
               var watButPress = detectWhatButtonPressed(gamepads,selPad);
               if(watButPress != -1){
                    // only if this button isn't already used
                    if(!buttonMapping.includes(watButPress)){
                        buttonMapping[gamePadMode] = watButPress;
                        axesMapping[gamePadMode] = [-1,-1] // set this to be a button
                        // incrment mode
                        gamePadMode+=1; 
                        if(gamePadMode == CalibrationOrder.length){
                            gamePadMode = -2;
                            document.getElementById("CalibrationState").innerHTML = "Calibration complete!";
                        }
                    }
               }
               //detect changes in axes
               var whatAxisAndMax = detectAxisMovment(gamepads,selPad);
               if(whatAxisAndMax[0] != -1){
                    // handle the detection if this value was already used
                    alreadyHaveThisValue = false;
                    for(var i = 0; i < axesMapping.length; i++){
                        var val1 = axesMapping[i][0];
                        var val2 = axesMapping[i][1];
                        if(val1 == whatAxisAndMax[0] && val2 == whatAxisAndMax[1]){ // already in there
                            alreadyHaveThisValue = true
                        }
                    }
                    // if it hasn't been used save it, advance to next button
                    if(alreadyHaveThisValue == false){
                        // console.log(axesMapping);
                        buttonMapping[gamePadMode] = -1 // set this to no button and its an axes
                        axesMapping[gamePadMode] = whatAxisAndMax;
                        // incrment mode
                        gamePadMode+=1;
                        if(gamePadMode == CalibrationOrder.length){
                            gamePadMode = -2;
                            document.getElementById("CalibrationState").innerHTML = "Calibration complete!";
                        }
                    }
               }

            } else{ // game pad is less than -1 and -2 is full calibrated
                if(gamePadMode  == -2){
                    listOfPadVals = getGamePadCaledData(gamepads,selPad);
                }
                // console.log(listOfPadVals);
            }

            
        }
        // on change of selected pad status
        if(selPad != last_selPad){
            var padStatString = "No gamepad selected, "+String(gamepads.length)+" gamepads found";
            if(selPad >= 0){
                padStatString = "Using gamepad "+String(selPad);
                zeroAxes(gamepads,selPad); // get the zero of the axis
            }
            document.getElementById("gamePadStatusText").innerHTML = padStatString;
        }
        last_selPad = selPad; 
    // }
    // catch(err) {
        // document.getElementById("gamePadStatusText").innerHTML = "Error with gamepads: "+String(err);
    // }
     
  }
      

function getGamePadCaledData(gamepadData,whatPad){
    var gamepadOUT = [];
    var buttons = gamepadData[whatPad].buttons
    var axes = gamepadData[whatPad].axes
    for(var i = 0; i < CalibrationOrder.length; i++){
        butt_I = buttonMapping[i];
        axes_I = axesMapping[i][0];
        axesMax_val = axesMapping[i][1];
        if(butt_I != -1){gamepadOUT.push(make2Dec(buttons[butt_I].value ));}
        else{
            
            var temp = [make2Dec(axes[axes_I]),make2Dec(axesMax_val)]
            gamepadOUT.push(temp);
        }
    }
    return(gamepadOUT);
}

function make2Dec(value){
    return Math.round(value*100)/100;
}
  


function detectWhatButtonPressed(gamepadData,whatPad){
    //buttons
    var buttons = gamepadData[whatPad].buttons
    for (var i = 0; i < buttons.length; i++) {
        var pressDetect = buttons[i].touched
        if(pressDetect == 1){
            return i;
        }
    }
    return -1;
}


var axesZeroVals = [];
function zeroAxes(gamepadData,whatPad){
    //buttons
    var axes = gamepadData[whatPad].axes
    // console.log(axes)
    for (var j = 0; j < axes.length; j++) {
        axesZeroVals[j] = axes[j]
    }
    
    return -1;
}

var lastDiff = 0;
function detectAxisMovment(gamepadData,whatPad){
    //buttons
    var axes = gamepadData[whatPad].axes
    // console.log(axes)
    for (var j = 0; j < axes.length; j++) {
        var ax = axes[j]
        var diff = ax-axesZeroVals[j];
        if(Math.abs(diff) > .05){ // probable change detected
            if(Math.abs(diff-lastDiff) < .01){ // stable?
                return [j,diff];
            }
            lastDiff = diff;
        }
        
    }
    
    return [-1,-1];
}

 function FindActiveGamepad(gamepadData){
    for (var i = 0; i < gamepadData.length; i++) {
        //buttons
        var buttons = gamepadData[i].buttons
        for (var j = 0; j < buttons.length; j++) {
            var pressDetect = buttons[j].touched
            if(pressDetect == 1){
                return i;
            }
        }
    }
    return -1;
 }

 
  
  