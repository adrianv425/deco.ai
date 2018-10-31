function redirect(){
    var newp = document.getElementById("newIP").value;
    location.replace("/nodes/register/" + newp);
}