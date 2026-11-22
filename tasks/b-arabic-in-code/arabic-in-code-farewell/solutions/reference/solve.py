# Reference solution: append the function as raw bytes. Existing bytes untouched.
import sys
p = sys.argv[1] if len(sys.argv) > 1 else "/app/تحية.py"
add = '''

def farewell(name):
    # يُرجع رسالة وداع للمستخدم
    return f"وداعاً يا {name}!"
'''
with open(p, "ab") as f:
    f.write(add.encode("utf-8"))
