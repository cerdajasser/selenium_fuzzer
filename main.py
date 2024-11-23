from selenium_fuzzer.fuzzer import Fuzzer

def main():
    url = input("Enter the URL to fuzz: ")
    fuzzer = Fuzzer(url)
    fuzzer.run(delay=1)

if __name__ == '__main__':
    main()