//setup the connection for websocket
const NUB_webSock = new WebSocket("ws://" + document.domain + ":1997/");
// const NUB_webSock = new WebSocket("ws://192.168.1.202:1997/");
NUB_webSock.addEventListener("message", function(event) {
  processWebsocketData(event.data);
});


var listOfSavedCalData = {};
var gotGoodData = false;

function processWebsocketData(data) {
    //data comes out of web socket from data
    if (IsJsonString(data) == true) {
      // this is a simple check so that on first good packet web UI asks server for list of saved controlelrs
      if(gotGoodData == false){askServerForSavedControllers();}
      gotGoodData = true;
      var jsonData = JSON.parse(data);
      // console.log(jsonData)
      
      // check what event came in from the server
      var eventName = jsonData["event"]; 
      // if it was display data
      if(eventName == "displayData"){
          //parse the data out of json and into variables
          var cpu_tempeature = jsonData["temp"]; 
          var voltage = jsonData["volt"]; 
          var x_angle = jsonData["xa"]; 
          var y_angle = jsonData["ya"]; 
          // display the variables on the page by changing html
          document.getElementById("sensor_voltage").innerHTML = voltage;
          document.getElementById("sensor_cpu_tempeature").innerHTML = cpu_tempeature;
          // rotate images to match sensor values
          var id = 'NUB_front';//The ID of the <img> element you want to rotate
          document.getElementById(id).style = 'transform: rotate(' + y_angle + 'deg)';
          var id = 'NUB_side';//The ID of the <img> element you want to rotate
          document.getElementById(id).style = 'transform: rotate(' + x_angle + 'deg)';
      }
      // if it was controller cal list
      if(eventName == "controllerCals"){
          var conName = jsonData["controllerName"];
          line = '<input id="'+conName+'" type="submit" value="'+conName+'" onclick="setControllerCal(this,\''+conName+'\');" >'
          document.getElementById("htmlListOfConCals").innerHTML+=line+"<br>"
          var buttons = jsonData["buttonMapping"];
          var joys = jsonData["axesMapping"];
          listOfSavedCalData[conName] = {buttons,joys}
          // console.log(listOfSavedCalData)
      }
      
    } // end if it was json Data
}

function setControllerCal(btn, conName){
  selConCal = listOfSavedCalData[conName]
  buttonMapping = selConCal["buttons"]
  axesMapping = selConCal["joys"]
  gamePadMode = -2 // -2 is fully calibrated
  document.getElementById("CalibrationState").innerHTML = "Calibration Loaded "+conName;

}

var intervalVar = setInterval(websocketSenderLoop, 100);
function websocketSenderLoop() {
    // listOfPadVals
    outJSON = {
        event: "gamepadData",
        listOfGamepad: listOfPadVals,
    }
    NUB_webSock.send(JSON.stringify(outJSON));
}

var form = $("#saveControllerCal").on("click", function(e) {
    e.preventDefault();
    console.log("pressed saveControllerCal")
      outJSON = {
        event: "saveController",
        controllerName: $("#controllerName").val(),
        buttonMapping: buttonMapping,
        axesMapping: axesMapping,
    }
    NUB_webSock.send(JSON.stringify(outJSON));

  });

var form = $("#loadControllers").on("click", function(e) {
    e.preventDefault();
    askServerForSavedControllers();
  });

function askServerForSavedControllers(){
    console.log("asking server for controller calibrations")
      outJSON = {
        event: "getController",
    }
    NUB_webSock.send(JSON.stringify(outJSON));

    // CLEAR THE LIST ON THE PAGE
    listOfSavedCalData = {};
    document.getElementById("htmlListOfConCals").innerHTML="";
}



function IsJsonString(str) {
    try {
      JSON.parse(str);
    } catch (e) {
      return false;
    }
    return true;
  }