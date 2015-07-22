var offset = 0;
var currentSync = 0;

Date.prototype.format = function(format) {
    var returnStr = '';
    var replace = Date.replaceChars;
    for (var i = 0; i < format.length; i++) {       var curChar = format.charAt(i);         if (i - 1 >= 0 && format.charAt(i - 1) == "\\") {
            returnStr += curChar;
        }
        else if (replace[curChar]) {
            returnStr += replace[curChar].call(this);
        } else if (curChar != "\\"){
            returnStr += curChar;
        }
    }
    return returnStr;
};

Date.replaceChars = {
    H: function() { return (this.getHours() < 10 ? '0' : '') + this.getHours(); },
    i: function() { return (this.getMinutes() < 10 ? '0' : '') + this.getMinutes(); },
    s: function() { return (this.getSeconds() < 10 ? '0' : '') + this.getSeconds(); },
};


function syncTime() {
	
    // Set up our time object, synced by the HTTP DATE header
    // Fetch the page over JS to get just the headers
    console.log("syncing time")
    var r = new XMLHttpRequest();
    var start = (new Date).getTime();
    var localSync = currentSync;

    r.open('HEAD', document.location);
    r.onreadystatechange = function()
    {
        if (r.readyState != 4 || currentSync != localSync)
        {
            return;
        }
        currentSync++;
        var latency = (new Date).getTime() - start;
        var timestring = r.getResponseHeader("DATE");

        // Set the time to the **slightly old** date sent from the 
        // server, then adjust it to a good estimate of what the
        // server time is **right now**.
        var systemtime = new Date(timestring);
        systemtime.setMilliseconds(systemtime.getMilliseconds() + (latency / 2))
	    offset = systemtime - (new Date).getTime();
    };
    r.send(null);
}

function getClockString() {
	var res = new Date();
	res.setMilliseconds(res.getMilliseconds() + offset);
	return res.format('H:i:s');
}

function updateClock() {
	document.getElementById('clock').innerHTML = 'Server time: ' + getClockString();
}

syncTime();
setInterval(syncTime, 60000);

setInterval(updateClock, 100);
