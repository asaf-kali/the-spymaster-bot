def handle(*args, **kwargs):
    print(f"args: {args}, kwargs: {kwargs}")
    return {"statusCode": 200, "body": "Hello from Lambda!"}


def main():
    handle()


if __name__ == "__main__":
    main()
