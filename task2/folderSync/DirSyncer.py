import os
import shutil
import filecmp
import logging
import threading

class DirComparator:
    def __init__(self, intersection, sourceOnly, targetOnly):
        self.intersection = intersection
        self.sourceOnly = sourceOnly
        self.targetOnly = targetOnly



class DirSyncer:
    def __init__(self, src, dst, interval, logFile):
        self.src = src
        self.dst = dst
        self.interval = interval
        logging.basicConfig(filename=logFile, level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def startSync(self):
        self.sync()
        threading.Timer(self.interval, self.startSync).start()

    def sync(self):
        print("Synchronizing directories {0} and {1}".format(self.src, self.dst))
        self.updateTarger(self.src, self.dst)
        

    def compare(self, src, dst):
        d1 = set()
        d2 = set()

        for root, dirs, files in os.walk(src):
            for f in dirs + files:
                path = os.path.relpath(os.path.join(root, f), src)
                d1.add(path)
        
        for root, dirs, files in os.walk(dst):
            for f in dirs + files:
                path = os.path.relpath(os.path.join(root, f), dst)
                d2.add(path)

        intersection = d1.intersection(d2)
        onlyD1 = d1.difference(intersection)
        onlyD2 = d2.difference(intersection)

        return DirComparator(intersection, onlyD1, onlyD2)
                

    def updateTarger(self, src, dst):
        dirComparator = self.compare(src, dst)
        
        #remove files and directories from target which are not in source
        for path in dirComparator.targetOnly:
            absPath = os.path.join(dst, path)
            if os.path.isfile(absPath):
                try:
                    os.remove(os.path.join(dst, path))
                    logging.info("Removed file {0} from {1}".format(path, dst))
                except OSError:
                    print("Error: can't remove file " + absPath)
                    logging.error("Cannot removed file {0} from {1}".format(path, dst))
            elif os.path.isdir(absPath):
                try:
                    shutil.rmtree(absPath)
                    logging.info("Removed directory {0} from {1}".format(path, dst))
                except shutil.Error:
                    print("Error: can't remove directory " + absPath)
                    logging.error("Cannot removed directory {0} from {1}".format(path, dst))

        #copy files and directories from source to target
        for path in dirComparator.sourceOnly:
            absPath = os.path.join(src, path)
            if os.path.isfile(absPath):
                relDir = os.path.dirname(path)
                dir2 = os.path.join(dst, relDir)
                try:
                    if not os.path.exists(dir2):
                       try:
                           os.makedirs(dir2, exist_ok=True)
                       except OSError:
                        print("Error: can't create directory FOR FILE" + dir2)
                        logging.error("Cannot create directory {0} for file {1}".format(dir2, absPath))
                    shutil.copy(absPath, dir2)
                    logging.info("Copied file {0} from {1} to {2}".format(path, src, dst))
                except shutil.Error:
                    print("Error: can't copy file " + absPath)
            elif os.path.isdir(absPath):
                try:
                    os.makedirs(os.path.join(dst, path), exist_ok=True)
                except OSError:
                    print("Error: can't create directory DIR" + os.path.join(dst, path))
                    logging.error("Cannot create directory {0} from {1}".format(path, dst))

        #if necessary, update files and directories in target

        for path in dirComparator.intersection:
            absPath = os.path.join(src, path)
            absPath2 = os.path.join(dst, path)
            if os.path.isfile(absPath):
                if os.path.getmtime(absPath) > os.path.getmtime(absPath2) or not filecmp.cmp(absPath, absPath2):
                    try:
                        shutil.copy(absPath, absPath2)
                        logging.info("Updated file {0} from {1} to {2}".format(path, src, dst))
                    except shutil.Error:
                        print("Error: can't copy file " + absPath)
                        logging.error("Cannot copy file {0} from {1} to {2}".format(path, src, dst))
          
                    