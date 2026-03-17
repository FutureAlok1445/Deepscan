import mesonet
print(dir(mesonet))
try:
    model = mesonet.Meso4()
    print("Meso4 loaded")
except Exception as e:
    print(f"Meso4 failed: {e}")
