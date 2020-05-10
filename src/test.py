import argparse
import numpy as np
import os
import pdb
import torch
import torchvision
from torch.autograd import Variable
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import datasets, models, transforms
from tqdm import tqdm

from dataset import *
from model import BaselineModel, OurModel
from utils import *

def main():
    pdb.set_trace()

    # Determine device
    device = getDevice(opt.gpu_id)

    # Create data loaders
    data_loaders = load_celeba(splits=['valid'], batch_size=opt.batch_size, subset_percentage=opt.subset_percentage)
    test_data_loader = data_loaders['valid']

    # Load checkpoint
    checkpoint = torch.load(opt.weights, map_location=device)

    # Create model
    model = BaselineModel(checkpoint['hyp']['hidden_size'])

    # Convert device
    model = model.to(device)

    test_batch_count = len(test_data_loader)

    # Load model
    model.load_state_dict(checkpoint['model'])    

    # Evaluate
    model.eval()

    # Initialize meters
    mean_accuracy = AverageMeter()
    mean_equality_gap_0 = AverageMeter()
    mean_equality_gap_1 = AverageMeter()
    mean_parity_gap = AverageMeter()

    with tqdm(enumerate(test_data_loader), total=test_batch_count) as pbar:
        for i, (images, targets, genders) in pbar:
            images = Variable(images.to(device))
            targets = Variable(targets.to(device))
            genders = Variable(genders.to(device))

            with torch.no_grad():
                # Forward pass
                outputs = model(images)
                targets = targets.type_as(outputs)

                # Calculate accuracy
                eval_acc = calculateAccuracy(outputs, targets)

                # Calculate fairness metrics
                eval_equality_gap_0, eval_equality_gap_1 = calculateEqualityGap(outputs, targets, genders)
                eval_parity_gap = calculateParityGap(outputs, targets, genders)

                # Update averages
                mean_accuracy.update(eval_acc, images.size(0))
                mean_equality_gap_0.update(eval_equality_gap_0, images.size(0))
                mean_equality_gap_1.update(eval_equality_gap_1, images.size(0))
                mean_parity_gap.update(eval_parity_gap, images.size(0))

                s_test = ('Accuracy: %.4f, Equality Gap 0: %.4f, Equality Gap 1: %.4f, Parity Gap: %.4f') % (mean_accuracy.avg, mean_equality_gap_0.avg, mean_equality_gap_1.avg, mean_parity_gap.avg)
                pbar.set_description(s_test)


        # Log results
        with open(opt.log, 'a+') as f:
            f.write('{}\n'.format(s_test))

    print('Done!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # parser.add_argument('--dataset', type=str, required=True, help='dataset path. Must contain training_set and eval_set subdirectories.')
    parser.add_argument('--subset-percentage', type=float, required=False, default=1.0, help='Fraction of the dataset to use')
    parser.add_argument('--weights', '-w', type=str, required=True, help='weights to preload into model')
    parser.add_argument('--batch-size', type=int, required=False, default=16, help='batch size')
    parser.add_argument('--log', type=str, required=False, default='test.log', help='path to log file')
    parser.add_argument('--gpu-id', type=int, required=False, default=0, help='GPU ID to use')
    opt = parser.parse_args()
    main()
