// Have to add defer to <script> tag in html file
// so document.querySelector() can work properly
const days = document.querySelector(".days"),
prevnextIcon = document.querySelectorAll(".icons span"),
currentDate = document.querySelector(".current-date"),
dates = document.getElementsByClassName("date-number");



// Build the Date to be passed on to python file
// Year-Month-Date
let buildDate = "";

// Keeps variable even after page refresh
let clickedDate = sessionStorage.getItem("clickedDate");

// Gets the current date
let date = new Date(),
currYear = date.getFullYear(),
currMonth = date.getMonth();

const months = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "February"]

const renderCalendar = () =>{
    
    console.log(buildDate);
    let lastDateofMonth = new Date(currYear, currMonth + 1, 0).getDate(),//gets last date of month
    lastDateofLastMonth = new Date(currYear, currMonth, 0).getDate(),//gets last date of last month
    firstDayOfMonth = new Date(currYear, currMonth, 1).getDay();//gets first day of month
    let liTag = "";
    
    for(let i = firstDayOfMonth; i > 0; i--){
        liTag += `<li class="inactive">${lastDateofLastMonth - i + 1}</li>`;
    }

    for(let i = 1; i <= lastDateofMonth; i++){
        let isToday = i === date.getDate() && currMonth === new Date().getMonth()
                        && currYear === new Date().getFullYear() ? "active" : "";
        // shortened if statement
        let isClicked = i == clickedDate ? "active current" : "";
        
        console.log(`CLICKED DATE: ${clickedDate}`);
        console.log(`INDEX: ${i}`);
        console.log(`isClicked: ${isClicked}`)
        liTag += `<li class="${isToday} ${i} ${isClicked}"><a class = "date-number">${i}</a></li>`; // adds a <li> element for every day in the month
        
    }
    currentDate.innerText = `${months[currMonth]} ${currYear}`;
    days.innerHTML = liTag;
    
}
renderCalendar();
prevnextIcon.forEach(icon => {
    icon.addEventListener("click", () => {
        
        
        //shortened if statement
        currMonth = icon.id === "prev" ? currMonth -1 : currMonth +1;
        if(currMonth < 0 || currMonth > 11){
            date = new Date(currYear, currMonth);
            currYear = date.getFullYear();
            currMonth = date.getMonth();
        }
        else{
            date = new Date();
        }
        renderCalendar();
    })
})
for(let i =0; i < dates.length; i++){
    // If element is clicked it gets highlighted to a different
    // color
    dates[i].addEventListener("click", function(){
        newFunc(i);
        
        clickedDate = (i+1).toString();
        sessionStorage.setItem("clickedDate", clickedDate);
        location.reload();
        
    }
    )
}

// Function that gives the date to the python file
// So that we can use it there
function newFunc(num){
    buildDate = `${currYear}-${addZero(currMonth+1)}-${addZero((num+1))}`;
    console.log(buildDate);
    console.log("{{user.1}}");
    $.ajax({ 
        url: '/process', 
        type: 'POST', 
        contentType: 'application/json', 
        data: JSON.stringify({ 'value': buildDate }), 
        error: function(error) { 
            console.log(error); 
        } 
    });
    
}

function addZero(num){
    
    switch(num.toString()){
        case '1':
            return '01';
        case '2':
            return '02';
        case '3':
            return '03';   
        case '4':
            return '04';
        case '5':
            return '05';
        case '6':
            return '06';
        case '7':
            return '07';
        case '8':
            return '08';
        case '9':
            return '09';
        default:
            return num.toString();
    }
}





