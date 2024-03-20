#converts date to a 3 element string array
def date_to_string(date):
    date = date.split('-')
    def month_to_string(month):
        if month == '01':
            return 'Jan'
        elif month == '02':
            return 'Feb'
        elif month == '03':
            return 'Mar'
        elif month == '04':
            return 'Apr'
        elif month == '05':
            return 'May'
        elif month == '06':
            return 'Jun'
        elif month == '07':
            return 'Jul'
        elif month == '08':
            return 'Aug'
        elif month == '09':
            return 'Sep'
        elif month == '10':
            return 'Oct'
        elif month == '11':
            return 'Nov'
        elif month == '12':
            return 'Dec'
        else:
            return 'invalid number'
    date[1] = month_to_string(date[1])
    return date

def date_to_string_FULL(date):
    date = date.split('-')
    def month_to_string(month):
        if month == '01':
            return 'January'
        elif month == '02':
            return 'February'
        elif month == '03':
            return 'March'
        elif month == '04':
            return 'April'
        elif month == '05':
            return 'May'
        elif month == '06':
            return 'June'
        elif month == '07':
            return 'July'
        elif month == '08':
            return 'August'
        elif month == '09':
            return 'September'
        elif month == '10':
            return 'October'
        elif month == '11':
            return 'November'
        elif month == '12':
            return 'December'
        else:
            return 'invalid number'
    date[1] = month_to_string(date[1])
    return date

#converts kelvin to degrees
def keltoC(degrees):
    return degrees - 273.15