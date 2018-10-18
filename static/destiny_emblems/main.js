var emblems = document.getElementById("emblems");
emblems.addEventListener("mouseover", function(e) {
    if (e.target.nodeName == "IMG" && e.target.classList.contains("emblem-icon-img")) {
        let emblem = e.target.parentNode.parentNode;
        let tooltip = document.getElementById("emblem_tooltip");
        document.getElementById("emblem_tooltip_name").innerHTML = emblem.title;
        document.getElementById("emblem_tooltip_icon").src = emblem.dataset.icon;
        document.getElementById("emblem_tooltip_header").className = emblem.dataset.tier.toLowerCase();
        document.getElementById("emblem_tooltip_tier").innerHTML = emblem.dataset.tier;
        if (emblem.dataset.mainObjective) {
            document
                .getElementById("emblem_tooltip_objective")
                .innerHTML = (emblem.dataset.mainProgress ? emblem.dataset.mainProgress + " // " : "")
                    + emblem.dataset.mainObjective;
            document.getElementById("emblem_tooltip_objective").classList.remove("hidden");
            document.getElementById("emblem_tooltip_objective_small").innerHTML = emblem.dataset.mainProgress;
        } else {
            document.getElementById("emblem_tooltip_objective").innerHTML = "";
            document.getElementById("emblem_tooltip_objective").classList.add("hidden");
            document.getElementById("emblem_tooltip_objective_small").innerHTML = "Level " + document.getElementById("emblem_tooltip_objective_small").dataset.level;
        }
        tooltip.style.top = (e.target.offsetTop + 20) + "px";
        tooltip.style.left = (e.target.offsetLeft + 20) + "px";
        tooltip.classList.remove("hidden");
    }
});
/*emblems.addEventListener("mouseout", function(e) {
    if (e.target.nodeName == "IMG") {
        let tooltip = document.getElementById("emblem_tooltip");
        document.getElementById("emblem_tooltip_name").innerHTML = "";
        document.getElementById("emblem_tooltip_icon").src = "";
        tooltip.classList.add("hidden");
    }
});*/

document.getElementById("save").onclick = function() {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    var playerData = document.getElementById("player_data").value;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "", true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader("X-CSRFToken", csrftoken);
    xhr.send(JSON.stringify({
        playerData: playerData
    }));
    xhr.onload = function() {
        console.log(this.responseText);
        //var data = JSON.parse(this.responseText);
        //console.log(data);
    }
}