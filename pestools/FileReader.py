import os
import pandas as pd

# Filereader.py
class FileReader(object):
    """
    A file-reading object to be used with "with". Good for reading Fortran-type input files. Opens
    file in binary mode ('rb') to ensure correct values of file.tell() in Windows. Source:
    https://docs.python.org/release/2.6.7/library/stdtypes.html?highlight=readline#file.tell

    Parameters
    ----------
        filename: str
            Name of the file to be open and read
        st_size: int
            Byte length of file when opened. Currently used to determine EOF

    Attributes
    ----------
        fileobject: file
            The open file object. Important when using tools like pd.read_table()
            with a FileReader object (e.g., pd.read_table(f.fileobject, ...))

    Methods
    ----------
        eof_check()
        get_cleanline()
        get_DataFrame()
        skiplines()
        nextline()
        find_phrase()
        get_datadist()

    Notes
    ----------

    """
    def __init__(self, filename):
        self.filename = filename

    def __enter__(self):
        self.fileobject = open(self.filename, 'rb')
        self.st_size = os.fstat(self.fileobject.fileno()).st_size
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.fileobject.close()

    def eof_check(self):
        """
        Looks at current byte position to figure out whether EOF has been reached
        Works, assuming the file isn't being added to while being read!
        True if end of file (EOF) has been reached, false if otherwise.

        Note: might want to change this because it could be adventageous to run this WHILE pest is
        writing a file. Or at least offer multiple ways to calculate. The second method is
        to use fileobject.read(X) where X is a number of bytes, then check to see if that many bytes
        were returned.
        """
        curr_pos = self.fileobject.tell()

        if curr_pos >= self.st_size:
            return True
        else:
            return False

    def get_cleanline(self, pos=None):
        """ Returns a return-free line. If a position is specified, splits the line and returns
            only the position(s) (indeces) specified
        """
        line = self.fileobject.readline().strip()
        if pos is not None:
            line = line.split()[pos]  # type: int
        return line

    def get_DataFrame(self, manual_rewind=False, **kwargs):
        """ Pulls a table of data out of the open file, returns as dataframe.
            Arguments:
                manual_rewind: if True, "manually" moves the file pointer to the end of the table,
                               as based on kwarg "nrows". This is sometimes necessary because the
                               Pandas DataFrame reader sometimes ends up too far! A mystery.
                kwargs:        passed to pd.read_table()
        """
        if manual_rewind:
            if 'nrows' not in kwargs:
                # Perhaps would be best to just require nrows and always "manual_rewind"
                # Since calling this function without nrows would be rather rare
                raise TypeError('manual_rewind set to True, argument nrows required!')
        # Need this anyway for read exception
        last_pos = self.fileobject.tell()
        try:
            df = pd.read_table(self.fileobject, **kwargs)
        except(IndexError):
            # Text files can easily have extra columns lying around. If column names are
            # passed, this can cause an error. We will except this error by manually editing column
            # names post-read - LS 12/15/17
            self.fileobject.seek(last_pos)
            if 'names' in kwargs:
                colnames = kwargs.pop('names')
                kwargs['header'] = None
            else:
                if 'header' not in kwargs:
                    kwargs['header'] = None
                colnames = None
            df = pd.read_table(self.fileobject, **kwargs)
            if colnames is not None:
                rename_dict = dict(zip(df.columns.values[0:len(colnames)], colnames))
                df.rename(columns=rename_dict)
        if manual_rewind:
            self.fileobject.seek(last_pos)
            self.skiplines(kwargs['nrows'])
        return df

    def skiplines(self, lines):
        """Skips 'lines' number of lines in current file
        """
        for i in range(0, lines):
            self.fileobject.readline()

    def nextline(self):
        """ Finds next non-blank line
        """
        last_pos = self.fileobject.tell()
        line = self.fileobject.readline()

        while line.strip()=='':
            last_pos = self.fileobject.tell()
            line = self.fileobject.readline()
            if self.eof_check():
                raise EOFError("End of File Reached")
        self.fileobject.seek(last_pos)

    def find_phrase(self, phrase, rewind=False, case_sens=False):
        """ Finds next line containing the phrase.
            Rewind stops at line with the phrase, false moves to next line.
            case_sens toggles whether the match is case sensitive
        """

        if not case_sens: phrase = phrase.lower()

        while True:
            last_pos = self.fileobject.tell()
            line = self.fileobject.readline()
            if not case_sens: line = line.lower()
            if phrase in line:
                break
            if self.eof_check():
                raise EOFError("End of file reached without finding phrase: " + phrase)

        if rewind:
            self.fileobject.seek(last_pos)

    def get_datadist(self):
        """ Finds the distance to the next comment line, blank line, or EOF
        """
        counter = 0
        last_pos = self.fileobject.tell()
        for line in self.fileobject:
            if line.startswith(('C', 'c', '*')) or line == '':
                break
            if line.strip('\r\n ') == '':
                break
            counter += 1
        self.fileobject.seek(last_pos)
        return counter
