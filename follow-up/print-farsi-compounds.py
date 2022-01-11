#!/usr/bin/env python

def main():
    import sys
    for line in sys.stdin:
        for word in line.split():
            if '#' in word:
                print(word)
                for segment in word.split('#'):
                    print(segment)
                print()


if __name__ == '__main__':
    main()
