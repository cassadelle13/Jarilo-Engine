import re

prompt = 'Создай файл test.txt и напиши в него hello'
print('Prompt:', repr(prompt))

file_match = re.search(r'файл[а-я]* (\w+\.\w+)', prompt.lower())
content_match = re.search(r'напиши в него ([^ ]+)', prompt.lower())

print('File match:', file_match)
print('Content match:', content_match)

if file_match and content_match:
    print('Filename:', file_match.group(1))
    print('Content:', content_match.group(1))