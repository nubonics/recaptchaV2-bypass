import os
import hashlib


"""# Removing Duplicate Images Using Hashing"""


def file_hash(filepath):
    with open(filepath, 'rb') as reader:
        return hashlib.md5(reader.read()).hexdigest()


def remove_duplicate_images():
    image_directory = 'imgs'
    
    file_list = os.listdir(image_directory)
    print(len(file_list))

    duplicates = []
    hash_keys = dict()
    for index, filename in enumerate(os.listdir(image_directory)):
        if os.path.isfile(filename):
            with open(filename, 'rb') as reader:
                filehash = hashlib.md5(reader.read()).hexdigest()
            if filehash not in hash_keys:
                hash_keys[filehash] = index
            else:
                duplicates.append((index, hash_keys[filehash]))

    """# Delete Files After Printing"""
    for index in duplicates:
        os.remove(file_list[index[0]])


if __name__ == '__main__':
    remove_duplicate_images()
