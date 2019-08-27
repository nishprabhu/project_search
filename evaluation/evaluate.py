import os
import sys
import zipfile
from timeit import default_timer as timer
import ujson as json
import shutil
from tqdm import tqdm
import subprocess


temp_folder = ''  # Temporary folder that is created during evaluation and then deleted
path_to_dump = ''  # Path to data dump
index_folder = ''  # Path to index folder
query_file = ''  # Path to query file
output_folder = ''  # Folder where search outputs are stored
results_file = ''  # Path to results file (to store details like index size, run time etc.)
timeout_index = 180  # Timeout indexing after 3 minutes
timeout_search = 120  # Timeout search after 2 minutes


def time(function):
    '''Computes the runtime of function'''

    def wrapper(self, *args, **kwargs):
        start = timer()
        result = function(self, *args, **kwargs)
        end = timer()
        if function.__name__ == 'run_indexing':
            self.index_time = end - start
        else:
            raise('Trying to time unknown function.')
        return result
    return wrapper


class Evaluation(object):
    """Evaluate different aspects of the submission"""

    def __init__(self, filename):
        super(Evaluation, self).__init__()
        self.filename = filename
        self.roll_number = os.path.basename(filename).split('.')[0]
        self.unzip_success = None
        self.index_timeout = None
        self.index_sucess = None
        self.index_time = 0
        self.index_size = 0
        self.search_timeout = None
        self.search_success = None

    def unzip(self, path):
        '''Unzip zip file to temp_folder'''
        try:
            with zipfile.ZipFile(self.filename, 'r') as zip_ref:
                zip_ref.extractall(path)
        except Exception:
            self.unzip_success = False
        else:
            self.unzip_success = True

    @time
    def run_indexing(self):
        try:
            cwd = os.path.join(temp_folder, self.roll_number)
            command = ['bash', 'index.sh', path_to_dump, index_folder]
            result = subprocess.run(command, cwd=cwd, timeout=timeout_index, capture_output=True)
        except subprocess.TimeoutExpired:
            self.index_timeout = True
        else:
            self.index_timeout = False
            if result.returncode == 0:
                self.index_sucess = True
            else:
                self.index_sucess = False

    def check_size(self, path):
        '''Check size of index folder'''
        total_size = 0
        for root, dirs, files in os.walk(path):
            for file in files:
                filepath = os.path.join(root, file)
                # skip if it is symbolic link
                if not os.path.islink(filepath):
                    total_size += os.path.getsize(filepath)
        self.index_size = total_size

    def run_search(self):
        try:
            cwd = os.path.join(temp_folder, self.roll_number)
            output_file = os.path.join(output_folder, self.roll_number + '.txt')
            command = ['bash', 'search.sh', index_folder, query_file, output_file]
            result = subprocess.run(command, cwd=cwd, timeout=timeout_search, capture_output=True)
        except subprocess.TimeoutExpired:
            self.search_timeout = True
        else:
            self.search_timeout = False
            if result.returncode == 0:
                self.search_success = True
            else:
                self.search_success = False

    def to_json(self):
        '''Convert object to json so that it can be written to disk'''
        data = {'roll_number': self.roll_number,
                'unzip_success': self.unzip_success,
                'index_timeout': self.index_timeout,
                'index_sucess': self.index_sucess,
                'index_time': self.index_time,
                'index_size': self.index_size,
                'search_timeout': self.search_timeout,
                'search_success': self.search_success}
        return json.dumps(data)


def evaluate(submission):
    '''Run evaluation on a given submission'''
    submission.unzip(temp_folder)
    if submission.unzip_success:
        submission.run_indexing()
        if not submission.index_timeout and submission.index_sucess:
            submission.check_size(index_folder)
            submission.run_search()
    return


def run_cleanup(clean_output_folder=False, final_cleanup=False):
    '''Delete temporary folders'''
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    if os.path.exists(index_folder):
        shutil.rmtree(index_folder)
    if not final_cleanup:
        os.mkdir(index_folder)

    if clean_output_folder:
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.mkdir(output_folder)

    return


def main():
    submissions_folder = sys.argv[1]
    zip_files = os.listdir(submissions_folder)
    results = []
    run_cleanup(clean_output_folder=True)
    for zip_file in tqdm(zip_files):
        submission = Evaluation(os.path.join(submissions_folder, zip_file))
        evaluate(submission)
        results.append(submission.to_json())
        run_cleanup()
    run_cleanup(final_cleanup=True)

    with open(results_file, 'w') as file:
        for result in results:
            file.write(result)
            file.write('\n')


if __name__ == '__main__':
    main()
