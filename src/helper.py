import clipboard


def add_key(dictionary, string):
    clipboard.copy(string)
    qid = input(f"What is the qid for: {string} ?")
    dictionary[string] = qid
    return
