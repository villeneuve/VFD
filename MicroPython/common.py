# shared global variable accross modules

# When the time changes or is updated the daily program must be refreshed to be
# sync with the time. There are 3 ways to change time: LCD & buttons, web page
# and commands sent by uart. These are 3 different python modules. To inform
# the daily program process (main_3) we use the flag time_has_changed.
# because it's shared across modules we declare it here and import it in each
# module where it's needed.
time_has_changed = False

# Same thing for the list of tuples containing the daily program
# we declare it here and import it in each module where it's needed.
# progr = [(6, 0, 35), (7, 0, 25), (21, 0, 0)]  # liste de tuples
progr = []  # changed 24/08/2026 rmpty program
# defaut: start 35Hz a 6:00, 25Hz a 7:00 stop a 21:00
# format [(heure, minute, action), (heure, minute, action), etc..]

# when sent from uart the format must be a string strickly formated like this:
# [(6,0,35)-(7,0,25)-(21,0,0)] 
# no spaces allowed, a dash ("-") between tuples
# tuples starts ends with parenthesis
# each tuple contains 3 integers in the range 20~50 or 0
# the function str2tuple converts the string to the usable list of tuples.
