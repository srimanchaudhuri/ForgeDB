class A:
    def __repr__(self):
        return "A-repr"


class B:
    def __str__(self):
        return "B-str"


print(A())
print(repr(A()))
print(B())
print(repr(B()))
