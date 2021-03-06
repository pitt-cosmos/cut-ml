"""This script contains a few wrapper function to retrieve cut 
results from the pickle file generated by Loic and Rolando"""

import cPickle
import numpy as np
from get_tod import *

class CutResults:
    def __init__(self, path):
        """A utility class that process results from cut results from Loic
        :param:
            path: path to the pickle file that loic provides"""
        self._data = None
        self._path = path
        self.load()  # load pickle file from loic

    def load(self):
        """Load pickle file from the path specified"""
        with open(self._path, "r") as f:
            self._data = cPickle.load(f)
        
    def get_data(self, n, random=True):
        """Get tod names and labels of positive and negative
        :param:
            n: number of tods to be loaded
            random: if randomize is to be used
        :ret:
            filenames: list of tod names used for training
            labels: a list of the data labels for each tods 
        """
        n_data = len(self._data['name'])  # number of tods
        if random:  # randomize
            sel = np.random.choice(n_data, n)
        else:  # ordered
            sel = np.arange(n)
        filenames = [ self._data['name'][i] for i in sel]  # get filenames
        labels = self._data['sel'][:,sel]  # get labels for each tod 
        return filenames, labels

    def get_data_transform(self, n, downsample=0):
        """Load tod data and labels and transform to ML friendly format
        :param:
            n: number of tods to be used
            downsample: factor to downsample
        :ret:
            data_stack: numpy array of data for training
            label_stack: numpy array of data labels for training"""
        fnames, labels = self.get_data(n)
        # Retrieve and transform data
        data = get_tod_data_list(fnames, downsample)
        data_min_size = min([d.shape[1] for d in data])
        data_truncated = [d[:,:data_min_size] for d in data]  # be aware of truncation here
        data_stack = np.vstack(data_truncated)
        # data_stack = np.vstack(data)
        
        # Transform labels
        labels_stack = np.hstack([ labels[:,i] for i in np.arange(n)])
        return data_stack, labels_stack

    def get_data_learning(self, n_tod, n_sample, downsample=0, train_ratio=0.8):
        """Load data and split into training and testing set for ML
        :param:
            n_tod: number of tod to be used as input
            n_sample: number of positive samples (same as number of negative samples)
            downsample: factor of downsampling; 0: no downsample
            train_ratio: the ratio of data to be used as training set
        :ret:
            X_train: training data
            Y_train: training label
            X_test: testing data
            Y_test testing label"""
        data_stack, labels_stack = self.get_data_transform(n_tod, downsample)
        
        # in order to have good training, sample equally from good and bad
        print labels_stack
        good_ind = np.where(labels_stack==1)[0]
        bad_ind = np.where(labels_stack==0)[0]

        # sample evenly in both category
        print '[INFO] Random sampling from good detectors, N=%d' % n_sample
        good_sample = np.random.choice(good_ind, n_sample)
        print '[INFO] Random sampling from bad detectors, N=%d' % n_sample
        bad_sample = np.random.choice(bad_ind, n_sample)

        # split index
        print '[INFO] Splitting data into training set and testing set ...'
        split_index = int(n_sample * train_ratio)
        print '[INFO] Train: %d, \t Test: %d ' % (split_index*2, n_sample*2-split_index*2)
        
        # combine index
        train_ind = np.concatenate([good_sample[:split_index], bad_sample[:split_index]])
        test_ind = np.concatenate([good_sample[split_index:], bad_sample[split_index:]])
        
        # shuffle data order
        print '[INFO] Shuffling data ...'
        np.random.shuffle(train_ind)
        np.random.shuffle(test_ind)

        # generate training and test data
        print '[INFO] Generating training data ...'
        X_train = data_stack[train_ind, :]
        Y_train = labels_stack[train_ind]
        print '[INFO] Generating testing data ...'
        X_test = data_stack[test_ind,:]
        Y_test = labels_stack[test_ind]

        return X_train, Y_train, X_test, Y_test
