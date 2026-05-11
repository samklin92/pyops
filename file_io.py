# Writing to a file
with open("output.txt", "w") as f:
    f.write("Instance: i-0abc123\n")
    f.write("Region: us-east-1\n")
    f.write("Status: Running\n")

print("File written successfully")

# Reading it back
with open("output.txt", "r") as f:
    content = f.read()

print(content)