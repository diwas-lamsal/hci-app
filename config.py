def set_gesture_mode(mode = 'head'):
    with open('gesture.txt', 'w') as f:
        f.write(mode)

# https://www.guru99.com/python-file-readline.html#:~:text=Python%20readline()%20method%20reads,will%20return%20you%20binary%20object.
def get_gesture_mode():
    try:
        f = open("gesture.txt", "r")
        l = f.readline()
        f.close()
        return l
    except:
        return 'head'
