

function redirect(){
    var newp = document.getElementById("newIP").value;
    location.replace("/nodes/register/" + newp);
}

function newUpload(){
    var sender_public = document.getElementById("upload_sender_public").value;
    var sender_private = document.getElementById("upload_sender_private").value;
    var data = document.getElementById("upload_data").value;
    var contract = document.getElementById("upload_contract").value;
    var title = document.getElementById("upload_title").value;

    var httpReq = new XMLHttpRequest();

    httpReq.open("POST", "/transactions/upload", true);
    httpReq.setRequestHeader('Content-Type', 'application/json');
    httpReq.send(JSON.stringify({
        sender_public: sender_public,
        sender_private: sender_private,
        data: {
            method: 'SELL',
            code: data,
            title: title
        },
        contract: contract
    }))
    httpReq.onload = function(){
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "/mine", true)
        xhttp.setRequestHeader('Content-Type', 'application/json')
        xhttp.send()
        xhttp.onload = function(){
            location.replace("/transactions/uploads")
        }
    }

}

function run_ai(){
    var sender = document.getElementById("run_sender").innerHTML;
    var amount = document.getElementById("run_amount").innerHTML;
    var transactionID = document.getElementById("run_transactionID").innerHTML;
    var loop_count = document.getElementById("loop_count").innerHTML;
    var inputs = [];
    var i;
    for (i=0; i < loop_count; i++){
        inputs[i] = document.getElementById("input"+i).value;
        console.log("Found "+inputs[i])
    }

    var rhttp = new XMLHttpRequest();
    rhttp.open("POST", "/transactions/ai", true);
    rhttp.setRequestHeader('Content-Type', 'application/json');
    rhttp.send(JSON.stringify({
        sender: sender,
        amount: amount,
        transactionID: transactionID,
        inputs: inputs
    }))
    rhttp.onload = function(){
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "/mine", true)
        xhttp.setRequestHeader('Content-Type', 'application/json')
        xhttp.send()
        xhttp.onload = function(){
            location.replace("/transactions/ai/" + rhttp.response);
        }
    }
}

function confirmAI(){
    var transactionID = document.getElementById("run_transactionID").value;
    if (transactionID == undefined){
        transactionID = document.getElementById("run_transactionID").innerHTML;
    }
    location.replace("/transactions/confirm/" + transactionID);
}

function confirm_ai(transactionID){
    location.replace("/transactions/confirm/" + transactionID);
}

function getKey(){
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", "/key-pair", true)
    xhttp.setRequestHeader('Content-Type', 'application/json')
    xhttp.send()
    xhttp.onload = function(){
        document.getElementById("key").innerHTML = "<div class='container text-wrap'><h4 class='font-weight-bold' style='color: red;'>Please write this down and store it securely.</h4>";
        document.getElementById("key").innerHTML += xhttp.response;
        document.getElementById("key").innerHTML += "</div>";
        document.getElementById("getKey").innerHTML = "Get a different key";
    }
}

function getData(transactionID){
    location.replace("/transactions/training/" + transactionID)
}

function dataUpload(){
    var sender_public = document.getElementById("upload_sender_public").value;
    var sender_private = document.getElementById("upload_sender_private").value;
    var data = document.getElementById("data_upload").value;
    var contract = document.getElementById("upload_contract").value;
    var title = document.getElementById("data_title").value;

    var httpReq = new XMLHttpRequest();

    httpReq.open("POST", "/transactions/data-upload", true);
    httpReq.setRequestHeader('Content-Type', 'application/json');
    httpReq.send(JSON.stringify({
        sender_public: sender_public,
        sender_private: sender_private,
        data: {
            method: 'DATA',
            code: data,
            title: title
        },
        contract: contract
    }))
    httpReq.onload = function(){
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "/mine", true)
        xhttp.setRequestHeader('Content-Type', 'application/json')
        xhttp.send()
        xhttp.onload = function(){
            location.replace("/transactions/uploads")
        }
    }

}


function train_ai(transactionID){
    var sender = document.getElementById("run_sender").innerHTML;
    var transactionID = document.getElementById("run_transactionID").innerHTML;
    var training_data = document.getElementById("training_data").value;
    var rhttp = new XMLHttpRequest();
    rhttp.open("POST", "/transactions/train", true);
    rhttp.setRequestHeader('Content-Type', 'application/json');
    rhttp.send(JSON.stringify({
        sender: sender,
        transactionID: transactionID,
        training_data: training_data
    }))
    rhttp.onload = function(){
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "/mine", true)
        xhttp.setRequestHeader('Content-Type', 'application/json')
        xhttp.send()
        xhttp.onload = function(){
            location.replace("/transactions/train-complete/" + rhttp.response);
        }
    }
}