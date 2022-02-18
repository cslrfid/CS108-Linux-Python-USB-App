import time


def WaitForSeconds(seconds):
    for i in range(seconds, -1, -1):  
        time.sleep(1)
        print("\r>> Wait for {0:d} seconds".format(i), end="")