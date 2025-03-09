import textwrap

def split_text(text, max_length):
    return textwrap.wrap(text, width=max_length, break_long_words=False, replace_whitespace=False)

text = ("Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. ")
result = split_text(text, 30)

for line in result:
    print(repr(line))

