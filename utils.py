import time


def WaitForSeconds(seconds, tick=None):
    # tick(secondsLeft) is called once per second; without it, count down on the console
    for i in range(seconds, -1, -1):
        time.sleep(1)
        if tick:
            tick(i)
        else:
            print("\r>> Wait for {0:d} seconds".format(i), end="")
