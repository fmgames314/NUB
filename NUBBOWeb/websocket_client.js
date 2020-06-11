//setup the connection for websocket
const NUB_webSock = new WebSocket("ws://" + document.domain + ":1997/");
// const NUB_webSock = new WebSocket("ws://192.168.1.202:1997/");
NUB_webSock.addEventListener("message", function(event) {
  processWebsocketData(event.data);
});


function processWebsocketData(data) {
    //data comes out of web socket from data
    if (IsJsonString(data) == true) {
      var jsonData = JSON.parse(data);
      // console.log(jsonData)
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
}

var intervalVar = setInterval(websocketSenderLoop, 100);
function websocketSenderLoop() {
    listOfPadVals
    outJSON = {
        event: "gamepadData",
        listOfGamepad: listOfPadVals,
    }
    NUB_webSock.send(JSON.stringify(outJSON));
}


function IsJsonString(str) {
    try {
      JSON.parse(str);
    } catch (e) {
      return false;
    }
    return true;
  }