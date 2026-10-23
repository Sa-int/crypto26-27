import sys
ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

def normalize(text: str) -> str:
    text = text.lower()
    replaced = []
    for ch in text:
        if ch in ALPHABET:
            replaced.append(ch)
        else:
            replaced.append(" ")
    text = "".join(replaced)

    collapsed = []
    previous_was_space = False
    for ch in text:
        if ch == " ":
            if not previous_was_space:
                collapsed.append(ch)
            previous_was_space = True
        else:
            collapsed.append(ch)
            previous_was_space = False
    text = "".join(collapsed)
    return text.strip()

def main(path: str) -> None:
    with open(path, encoding="utf-8", errors="ignore") as f:
        text = f.read()

    normalized = normalize(text)

    with open("C:\\Users\\user\\Desktop\\Cryptography\\Lab1\\text_with_spaces.txt", "w", encoding="utf-8") as f:
        f.write(normalized)
    with open("C:\\Users\\user\\Desktop\\Cryptography\\Lab1\\text_no_spaces.txt", "w", encoding="utf-8") as f:
        f.write(normalized.replace(" ", ""))

if __name__ == "__main__":
    main(sys.argv[1])