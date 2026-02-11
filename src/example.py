def calc(a, b):
    x = 0
    if a > 0 and b>0:
        if a > b:
            x = a - b
        else:
            x = b - a
    return x
