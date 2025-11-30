def decorator(func):
    def inner(a,b):
        if a<b:
            a,b=b,a

        return func(a,b)
    return inner

div = lambda x,y: x/y

div1 = decorator(div)
ans = div1(2,4)
print(ans)