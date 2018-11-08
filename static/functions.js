

function redirect(){
    var newp = document.getElementById("newIP").value;
    location.replace("/nodes/register/" + newp);
}

function newUpload(){
    var sender = document.getElementById("upload_sender").value;
    var data = document.getElementById("upload_data").value;
    var contract = document.getElementById("upload_contract").value;
    var title = document.getElementById("upload_title").value;

    var httpReq = new XMLHttpRequest();

    httpReq.open("POST", "/transactions/upload", true);
    httpReq.setRequestHeader('Content-Type', 'application/json');
    httpReq.send(JSON.stringify({
        sender: sender,
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
    var rhttp = new XMLHttpRequest();
    rhttp.open("POST", "/transactions/ai", true);
    rhttp.setRequestHeader('Content-Type', 'application/json');
    rhttp.send(JSON.stringify({
        sender: sender,
        amount: amount,
        transactionID: transactionID
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