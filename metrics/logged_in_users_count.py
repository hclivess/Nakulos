import psutil

def collect():
    return len(psutil.users())

if __name__ == "__main__":
    user_count = collect()
    print(f"Number of logged-in users: {user_count}")