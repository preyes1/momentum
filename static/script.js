// Have to add defer to <script> tag in html file
// so document.querySelector() can work properly
const days = document.querySelector(".days")

// Gets the current date
let date = new Date(),
currYear = date.getFullYear(),
currMonth = date.getMonth();

const renderCalendar = () =>{
    let lastDateofMonth = new Date(currYear, currMonth + 1, 0).getDate()
    let liTag = "";

    for(let i = 1; i <= lastDateofMonth; i++){
        liTag += `<li>${i}</li>`; // adds a <li> element for every day in the month
    }
    days.innerHTML = liTag;
}
renderCalendar();