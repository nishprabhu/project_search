import sys


def read_file(query_file):
    '''Read query_file and return a list of queries'''
    with open(query_file, 'r') as file:
        queries = file.readlines()
    return queries


def write_file(outputs, output_file):
    '''outputs should be a list of lists.
        len(outputs) = number of queries
        Each element in outputs should be a list of titles corresponding to a particular query.'''
    with open(output_file, 'w') as file:
        for output in outputs:
            for line in output:
                file.write(line.strip() + '\n')
            file.write('\n')


def search(path_to_index_folder, queries):
    '''Write your code here'''
    pass


def main():
    path_to_index_folder = sys.argv[1]
    query_file = sys.argv[2]
    output_file = sys.argv[3]

    queries = read_file(query_file)
    outputs = search(path_to_index_folder, queries)
    write_file(outputs, output_file)


if __name__ == '__main__':
    main()
